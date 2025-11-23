# distribution/importer.py
from decimal import Decimal, InvalidOperation
from django.utils.dateparse import parse_date
from django.db import transaction
import pandas as pd
import math
from .models import Book, Category

def normalize_id(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        v = value.strip()
        return v if v != '' else None
    try:
        if isinstance(value, float) and not math.isnan(value):
            if value.is_integer():
                return str(int(value))
            else:
                return format(value, 'g')
        if isinstance(value, int):
            return str(value)
    except Exception:
        pass
    return str(value)

def parse_published_date(val):
    if pd.isna(val):
        return None
    try:
        # use pandas to parse common date formats (sample was MM/DD/YYYY)
        dt = pd.to_datetime(val, errors='coerce', dayfirst=False)
        if not pd.isna(dt):
            return dt.date()
    except Exception:
        pass
    try:
        return parse_date(str(val))
    except Exception:
        return None

def parse_decimal(val):
    if pd.isna(val):
        return Decimal('0.00')
    try:
        s = str(val).strip().replace(',', '')
        # handle empty strings
        if s == '':
            return Decimal('0.00')
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal('0.00')

@transaction.atomic
def import_books_from_dataframe(df, created_by=None):
    """
    Accepts a pandas DataFrame and imports rows into DB.
    Returns a dict: {'created': int, 'updated': int, 'skipped': int, 'errors': [str,...]}
    Expected (case-insensitive) columns:
      id, title, subtitle, authors, publisher, published_date, category, distribution_expense
    """
    # normalize column names
    df.columns = [str(c).strip() for c in df.columns]
    found_cols = [c.lower() for c in df.columns]

    # required minimal columns
    missing = [c for c in ['title', 'authors', 'category', 'distribution_expense'] if c not in found_cols]
    if missing:
        raise ValueError(f'Missing required columns: {missing}')

    created = updated = skipped = 0
    errors = []

    for idx, row in df.iterrows():
        # helper to get column by case-insensitive name
        def g(colname):
            for c in df.columns:
                if c.lower() == colname:
                    return row[c]
            return None

        raw_id = g('id')
        raw_title = g('title')
        raw_subtitle = g('subtitle')
        raw_authors = g('authors')
        raw_publisher = g('publisher')
        raw_published_date = g('published_date')
        raw_category = g('category')
        raw_distribution_expense = g('distribution_expense')

        # skip empty title rows
        if pd.isna(raw_title) or str(raw_title).strip() == '':
            skipped += 1
            continue

        try:
            source_id = normalize_id(raw_id)
            title = str(raw_title).strip()
            subtitle = None if pd.isna(raw_subtitle) else str(raw_subtitle).strip()
            authors = None if pd.isna(raw_authors) else str(raw_authors).strip()
            publisher = None if pd.isna(raw_publisher) else str(raw_publisher).strip()
            publishing_date = parse_published_date(raw_published_date)
            category_name = 'Uncategorized' if pd.isna(raw_category) or str(raw_category).strip() == '' else str(raw_category).strip()
            expense = parse_decimal(raw_distribution_expense)

            category_obj, _ = Category.objects.get_or_create(name=category_name)

            # dedupe by title + author (case-insensitive)
            qs = Book.objects.filter(title__iexact=title)
            if authors:
                qs = qs.filter(author__iexact=authors)

            book_data = {
                'author': authors or '',
                'publishing_date': publishing_date,
                'category': category_obj,
                'distribution_expenses': expense,   # model field name
            }
            # set optional fields if model has them
            # these will be ignored if your Book model doesn't define them
            book_data_extra = {}
            if hasattr(Book, 'source_id'):
                book_data_extra['source_id'] = source_id
            if hasattr(Book, 'subtitle'):
                book_data_extra['subtitle'] = subtitle
            if hasattr(Book, 'publisher'):
                book_data_extra['publisher'] = publisher

            # Merge
            book_data.update(book_data_extra)

            if qs.exists():
                book = qs.first()
                # update fields
                for k, v in book_data.items():
                    setattr(book, k, v)
                # stamp created_by if missing
                if created_by is not None and hasattr(Book, 'created_by') and not getattr(book, 'created_by', None):
                    book.created_by = created_by
                book.save()
                updated += 1
            else:
                create_kwargs = {**book_data, 'title': title}
                if created_by is not None and hasattr(Book, 'created_by'):
                    create_kwargs['created_by'] = created_by
                book = Book.objects.create(**create_kwargs)
                created += 1

        except Exception as e:
            errors.append(f'Row {idx}: {e}')
            skipped += 1
            # continue to next row
            continue

    return {'created': created, 'updated': updated, 'skipped': skipped, 'errors': errors}

def import_books_from_filelike(file_like, filename=None, created_by=None):
    """
    Accepts uploaded file-like object. Tries excel first, then csv.
    """
    try:
        # determine by filename if possible
        if filename and filename.lower().endswith(('.xls', '.xlsx')):
            file_like.seek(0)
            df = pd.read_excel(file_like, dtype=object)
        else:
            # try excel first; if fails, try csv
            try:
                file_like.seek(0)
                df = pd.read_excel(file_like, dtype=object)
            except Exception:
                file_like.seek(0)
                df = pd.read_csv(file_like, dtype=object)
    except Exception as e:
        raise ValueError(f'Could not read uploaded file: {e}')

    return import_books_from_dataframe(df, created_by=created_by)