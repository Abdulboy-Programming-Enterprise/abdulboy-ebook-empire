"""
Book Routes
===========
Book catalog management, search, and retrieval endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import Optional, List
from datetime import datetime
from app.core.database import get_db
from app.models.book import Book, BookStatus, Tag, BookTag
from app.models.user import User
from app.schemas.book import (
    BookCreate,
    BookUpdate,
    BookResponse,
    BookListResponse,
    BookSearchParams,
)
from app.schemas.response import StandardResponse
from app.api.deps import get_current_admin_user, get_current_user, get_optional_current_user
from app.utils.decorators import cache_result
from app.core.logger import logger
from app.tasks.email_jobs import send_new_book_notification

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("/", response_model=StandardResponse[BookListResponse])
async def list_books(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    language: Optional[str] = None,
    sort: str = Query("newest", regex="^(newest|price_asc|price_desc|popular)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    List published books with pagination and filtering.
    """
    # Build query
    query = select(Book).where(
        Book.status == BookStatus.PUBLISHED,
        Book.deleted_at.is_(None)
    )
    
    # Apply filters
    if category:
        query = query.join(Book.tags).where(Tag.slug == category)
    
    if min_price is not None:
        query = query.where(Book.price >= min_price)
    
    if max_price is not None:
        query = query.where(Book.price <= max_price)
    
    if language:
        query = query.where(Book.language == language)
    
    # Apply sorting
    if sort == "newest":
        query = query.order_by(Book.published_at.desc())
    elif sort == "price_asc":
        query = query.order_by(Book.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Book.price.desc())
    elif sort == "popular":
        query = query.order_by(Book.downloads_count.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    books = result.scalars().all()
    
    # Build response
    book_responses = []
    for book in books:
        # Get tags
        tag_result = await db.execute(
            select(Tag.name).join(BookTag).where(BookTag.book_id == book.id)
        )
        tags = tag_result.scalars().all()
        
        # Check if user has purchased this book
        has_purchased = False
        if current_user:
            from app.models.payment import UserBookPurchase
            purchase_result = await db.execute(
                select(UserBookPurchase).where(
                    UserBookPurchase.user_id == current_user.id,
                    UserBookPurchase.book_id == book.id
                )
            )
            has_purchased = purchase_result.scalar_one_or_none() is not None
        
        book_responses.append(BookResponse(
            id=str(book.id),
            title=book.title,
            slug=book.slug,
            description=book.description,
            author_name=book.author_name,
            author_id=str(book.author_id) if book.author_id else None,
            price=book.price,
            is_free=book.is_free,
            total_pages=book.total_pages,
            preview_pages=book.preview_pages,
            cover_image_url=book.cover_image_url,
            pdf_url=book.pdf_url if has_purchased else None,
            epub_url=book.epub_url if has_purchased else None,
            language=book.language,
            isbn=book.isbn,
            status=book.status.value,
            downloads_count=book.downloads_count,
            views_count=book.views_count,
            average_rating=None,  # TODO: Implement rating system
            review_count=0,
            tags=list(tags),
            published_at=book.published_at,
            created_at=book.created_at,
        ))
    
    return StandardResponse(
        success=True,
        data=BookListResponse(
            items=book_responses,
            total=total or 0,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit if total else 0,
        )
    )


@router.get("/search", response_model=StandardResponse[BookListResponse])
async def search_books(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort: str = Query("relevance", regex="^(relevance|newest|price_asc|price_desc|popular)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Search books by title, author, or description.
    """
    # Build search condition
    search_term = f"%{q}%"
    query = select(Book).where(
        Book.status == BookStatus.PUBLISHED,
        Book.deleted_at.is_(None),
        or_(
            Book.title.ilike(search_term),
            Book.author_name.ilike(search_term),
            Book.description.ilike(search_term),
        )
    )
    
    # Apply filters
    if category:
        query = query.join(Book.tags).where(Tag.slug == category)
    
    if min_price is not None:
        query = query.where(Book.price >= min_price)
    
    if max_price is not None:
        query = query.where(Book.price <= max_price)
    
    # Apply sorting
    if sort == "newest":
        query = query.order_by(Book.published_at.desc())
    elif sort == "price_asc":
        query = query.order_by(Book.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Book.price.desc())
    elif sort == "popular":
        query = query.order_by(Book.downloads_count.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    books = result.scalars().all()
    
    # Build response (same as list_books)
    book_responses = []
    for book in books:
        tag_result = await db.execute(
            select(Tag.name).join(BookTag).where(BookTag.book_id == book.id)
        )
        tags = tag_result.scalars().all()
        
        has_purchased = False
        if current_user:
            from app.models.payment import UserBookPurchase
            purchase_result = await db.execute(
                select(UserBookPurchase).where(
                    UserBookPurchase.user_id == current_user.id,
                    UserBookPurchase.book_id == book.id
                )
            )
            has_purchased = purchase_result.scalar_one_or_none() is not None
        
        book_responses.append(BookResponse(
            id=str(book.id),
            title=book.title,
            slug=book.slug,
            description=book.description,
            author_name=book.author_name,
            author_id=str(book.author_id) if book.author_id else None,
            price=book.price,
            is_free=book.is_free,
            total_pages=book.total_pages,
            preview_pages=book.preview_pages,
            cover_image_url=book.cover_image_url,
            pdf_url=book.pdf_url if has_purchased else None,
            epub_url=book.epub_url if has_purchased else None,
            language=book.language,
            isbn=book.isbn,
            status=book.status.value,
            downloads_count=book.downloads_count,
            views_count=book.views_count,
            average_rating=None,
            review_count=0,
            tags=list(tags),
            published_at=book.published_at,
            created_at=book.created_at,
        ))
    
    return StandardResponse(
        success=True,
        data=BookListResponse(
            items=book_responses,
            total=total or 0,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit if total else 0,
        )
    )


@router.get("/{book_id}", response_model=StandardResponse[BookResponse])
@cache_result(ttl=300, key_prefix="book_detail")
async def get_book(
    book_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Get book details by ID.
    """
    from sqlalchemy import select
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    
    if not book or book.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Increment view count
    book.views_count += 1
    await db.commit()
    
    # Get tags
    tag_result = await db.execute(
        select(Tag.name).join(BookTag).where(BookTag.book_id == book.id)
    )
    tags = tag_result.scalars().all()
    
    # Check if user has purchased this book
    has_purchased = False
    if current_user:
        from app.models.payment import UserBookPurchase
        purchase_result = await db.execute(
            select(UserBookPurchase).where(
                UserBookPurchase.user_id == current_user.id,
                UserBookPurchase.book_id == book.id
            )
        )
        has_purchased = purchase_result.scalar_one_or_none() is not None
    
    return StandardResponse(
        success=True,
        data=BookResponse(
            id=str(book.id),
            title=book.title,
            slug=book.slug,
            description=book.description,
            author_name=book.author_name,
            author_id=str(book.author_id) if book.author_id else None,
            price=book.price,
            is_free=book.is_free,
            total_pages=book.total_pages,
            preview_pages=book.preview_pages,
            cover_image_url=book.cover_image_url,
            pdf_url=book.pdf_url if has_purchased else None,
            epub_url=book.epub_url if has_purchased else None,
            language=book.language,
            isbn=book.isbn,
            status=book.status.value,
            downloads_count=book.downloads_count,
            views_count=book.views_count,
            average_rating=None,
            review_count=0,
            tags=list(tags),
            published_at=book.published_at,
            created_at=book.created_at,
        )
    )


@router.get("/{book_id}/preview")
async def get_book_preview(
    book_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get preview content for a book (first N pages).
    """
    from sqlalchemy import select
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    
    if not book or book.status != BookStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Return preview content (text or PDF URL)
    return StandardResponse(
        success=True,
        data={
            "title": book.title,
            "author": book.author_name,
            "preview_pages": book.preview_pages,
            "preview_content": book.preview_content,
            "preview_pdf_url": f"/api/v1/books/{book_id}/preview/pdf" if book.pdf_url else None,
        }
    )


@router.post("/", response_model=StandardResponse[BookResponse])
async def create_book(
    book_data: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Create a new book (Admin only).
    """
    from app.utils.helpers import generate_slug
    
    slug = generate_slug(book_data.title)
    
    new_book = Book(
        title=book_data.title,
        slug=slug,
        description=book_data.description,
        author_name=book_data.author_name,
        total_pages=book_data.total_pages,
        preview_pages=book_data.preview_pages,
        price=book_data.price,
        is_free=book_data.is_free,
        language=book_data.language,
        isbn=book_data.isbn,
        enable_watermark=book_data.enable_watermark,
        watermark_text=book_data.watermark_text,
        status=BookStatus.DRAFT,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    
    # Handle tags
    if book_data.tags:
        for tag_name in book_data.tags:
            # Find or create tag
            tag_result = await db.execute(
                select(Tag).where(Tag.name == tag_name)
            )
            tag = tag_result.scalar_one_or_none()
            if not tag:
                tag = Tag(
                    name=tag_name,
                    slug=generate_slug(tag_name),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(tag)
                await db.flush()
            
            # Create association
            book_tag = BookTag(
                book_id=new_book.id,
                tag_id=tag.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(book_tag)
        
        await db.commit()
    
    logger.info(f"Book created by admin {current_user.email}: {new_book.title}")
    
    return StandardResponse(
        success=True,
        message="Book created successfully",
        data=BookResponse(
            id=str(new_book.id),
            title=new_book.title,
            slug=new_book.slug,
            description=new_book.description,
            author_name=new_book.author_name,
            author_id=str(new_book.author_id) if new_book.author_id else None,
            price=new_book.price,
            is_free=new_book.is_free,
            total_pages=new_book.total_pages,
            preview_pages=new_book.preview_pages,
            cover_image_url=new_book.cover_image_url,
            pdf_url=None,
            epub_url=None,
            language=new_book.language,
            isbn=new_book.isbn,
            status=new_book.status.value,
            downloads_count=new_book.downloads_count,
            views_count=new_book.views_count,
            average_rating=None,
            review_count=0,
            tags=book_data.tags or [],
            published_at=new_book.published_at,
            created_at=new_book.created_at,
        )
    )


@router.put("/{book_id}", response_model=StandardResponse[BookResponse])
async def update_book(
    book_id: str,
    book_data: BookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Update an existing book (Admin only).
    """
    from sqlalchemy import select
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Update fields
    update_data = book_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "tags":
            continue
        setattr(book, field, value)
    
    book.updated_at = datetime.utcnow()
    
    # Update tags if provided
    if book_data.tags is not None:
        # Remove existing tags
        await db.execute(delete(BookTag).where(BookTag.book_id == book.id))
        
        # Add new tags
        for tag_name in book_data.tags:
            tag_result = await db.execute(
                select(Tag).where(Tag.name == tag_name)
            )
            tag = tag_result.scalar_one_or_none()
            if not tag:
                from app.utils.helpers import generate_slug
                tag = Tag(
                    name=tag_name,
                    slug=generate_slug(tag_name),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(tag)
                await db.flush()
            
            book_tag = BookTag(
                book_id=book.id,
                tag_id=tag.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(book_tag)
    
    await db.commit()
    await db.refresh(book)
    
    # Get updated tags
    tag_result = await db.execute(
        select(Tag.name).join(BookTag).where(BookTag.book_id == book.id)
    )
    tags = tag_result.scalars().all()
    
    logger.info(f"Book updated by admin {current_user.email}: {book.title}")
    
    return StandardResponse(
        success=True,
        message="Book updated successfully",
        data=BookResponse(
            id=str(book.id),
            title=book.title,
            slug=book.slug,
            description=book.description,
            author_name=book.author_name,
            author_id=str(book.author_id) if book.author_id else None,
            price=book.price,
            is_free=book.is_free,
            total_pages=book.total_pages,
            preview_pages=book.preview_pages,
            cover_image_url=book.cover_image_url,
            pdf_url=book.pdf_url,
            epub_url=book.epub_url,
            language=book.language,
            isbn=book.isbn,
            status=book.status.value,
            downloads_count=book.downloads_count,
            views_count=book.views_count,
            average_rating=None,
            review_count=0,
            tags=list(tags),
            published_at=book.published_at,
            created_at=book.created_at,
        )
    )


@router.delete("/{book_id}")
async def delete_book(
    book_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Soft delete a book (Admin only).
    """
    from sqlalchemy import select
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    book.deleted_at = datetime.utcnow()
    book.status = BookStatus.ARCHIVED
    await db.commit()
    
    logger.info(f"Book deleted by admin {current_user.email}: {book.title}")
    
    return StandardResponse(
        success=True,
        message="Book deleted successfully"
    )


@router.post("/{book_id}/publish")
async def publish_book(
    book_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Publish a book (Admin only).
    """
    from sqlalchemy import select
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    book.status = BookStatus.PUBLISHED
    book.published_at = datetime.utcnow()
    book.updated_at = datetime.utcnow()
    await db.commit()
    
    # Send notifications to subscribers
    send_new_book_notification.delay(book_id=str(book.id))
    
    logger.info(f"Book published by admin {current_user.email}: {book.title}")
    
    return StandardResponse(
        success=True,
        message="Book published successfully"
    )
