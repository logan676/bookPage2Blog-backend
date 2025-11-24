# BookPost Django Backend

Django REST API backend for BookPost - a web application for uploading book pages, extracting text via OCR, and creating annotated blog posts.

## Tech Stack

- **Django 5.0** - Web framework
- **Django REST Framework** - REST API
- **django-cors-headers** - CORS support for React frontend
- **Google Gemini AI** - OCR text extraction
- **django-storages + boto3** - Cloud storage (optional)
- **PostgreSQL** - Database (SQLite for development)

## Architecture

### Models

```
BlogPost
├── id (auto)
├── title
├── author
├── image (ImageField)
├── image_url (URLField for cloud storage)
├── created_at
└── updated_at

Paragraph
├── id (auto)
├── post (ForeignKey → BlogPost)
├── paragraph_id (order in document)
└── text

Idea
├── id (auto)
├── post (ForeignKey → BlogPost)
├── paragraph (ForeignKey → Paragraph)
├── quote (highlighted text)
├── note (user's thought)
├── created_at
└── updated_at
```

### API Endpoints

#### Blog Posts
- `GET /api/posts/` - List all posts
- `POST /api/posts/upload/` - Upload image + OCR + create post
- `GET /api/posts/{id}/` - Get single post with paragraphs and ideas
- `PUT /api/posts/{id}/` - Update post (title, author)
- `DELETE /api/posts/{id}/` - Delete post

#### Ideas
- `GET /api/ideas/?post={post_id}` - List ideas for a post
- `POST /api/ideas/` - Create new idea
- `PUT /api/ideas/{id}/` - Update idea
- `DELETE /api/ideas/{id}/` - Delete idea

## Setup Instructions

### 1. Prerequisites

- Python 3.9+
- pip and virtualenv
- Gemini API key (get from https://makersuite.google.com/app/apikey)

### 2. Installation

```bash
# Navigate to backend directory
cd bookPage2Blog-backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Required environment variables:
```bash
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
GEMINI_API_KEY=your-gemini-api-key-here
```

### 4. Database Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

The API will be available at: `http://localhost:8000/api/`

Admin panel: `http://localhost:8000/admin/`

## API Usage Examples

### Upload Image and Create Post

```bash
curl -X POST http://localhost:8000/api/posts/upload/ \
  -F "image=@/path/to/book_page.jpg" \
  -F "title=Chapter 1: Introduction" \
  -F "author=John Doe"
```

Response:
```json
{
  "id": 1,
  "title": "Chapter 1: Introduction",
  "author": "John Doe",
  "publishDate": "November 24, 2025",
  "imageUrl": "http://localhost:8000/media/book_pages/image.jpg",
  "content": [
    {
      "id": 1,
      "text": "The sun had barely kissed the horizon..."
    },
    {
      "id": 2,
      "text": "In the heart of the old library..."
    }
  ],
  "ideas": []
}
```

### Get Post with Ideas

```bash
curl http://localhost:8000/api/posts/1/
```

### Create New Idea

```bash
curl -X POST http://localhost:8000/api/ideas/ \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 1,
    "paragraphId": 2,
    "quote": "rewrite the stars themselves",
    "note": "A powerful metaphor for changing destiny."
  }'
```

Response:
```json
{
  "id": "1",
  "paragraphId": 2,
  "quote": "rewrite the stars themselves",
  "note": "A powerful metaphor for changing destiny.",
  "timestamp": "2025-11-24T10:00:00.000Z"
}
```

## OCR Processing

The backend uses **Google Gemini AI** for OCR text extraction. The workflow:

1. React uploads image file to `/api/posts/upload/`
2. Django saves image to temporary file
3. OCR service (`ocr_service.py`) sends image to Gemini API
4. Gemini extracts and returns text
5. Service parses text into logical paragraphs
6. Django creates BlogPost and Paragraph models
7. Returns structured JSON to React

### Switching to Google Cloud Vision

To use Google Cloud Vision instead of Gemini:

1. Install credentials: `pip install google-cloud-vision`
2. Download service account JSON from Google Cloud Console
3. Set environment variable: `GOOGLE_CLOUD_VISION_CREDENTIALS=/path/to/credentials.json`
4. Update `ocr_service.py` to set `use_gemini = False`

## Cloud Storage (Optional)

To use AWS S3 for image storage:

1. Set up AWS S3 bucket
2. Configure environment variables:
   ```bash
   USE_S3=True
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_STORAGE_BUCKET_NAME=your-bucket-name
   AWS_S3_REGION_NAME=us-east-1
   ```
3. Restart Django server

Images will be automatically uploaded to S3 and `image_url` will be populated.

## Testing

```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test bookpost_project.api.tests
```

## Deployment Considerations

### Production Settings

1. **Security**
   - Set `DEBUG=False`
   - Use strong `SECRET_KEY`
   - Configure `ALLOWED_HOSTS` properly
   - Enable HTTPS
   - Use environment variables for secrets

2. **Database**
   - Switch to PostgreSQL
   - Set up database backups

3. **Static/Media Files**
   - Use cloud storage (S3, GCS) for media files
   - Serve static files via CDN

4. **CORS**
   - Update `CORS_ALLOWED_ORIGINS` to production frontend URL

### Deployment Platforms

- **Heroku**: `git push heroku main`
- **Railway**: Connect GitHub repo
- **AWS EC2**: Use gunicorn + nginx
- **Google Cloud Run**: Deploy as container

## Project Structure

```
bookPage2Blog-backend/
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
└── bookpost_project/
    ├── __init__.py
    ├── settings.py        # Django settings
    ├── urls.py            # Main URL config
    ├── wsgi.py
    ├── asgi.py
    └── api/
        ├── __init__.py
        ├── models.py       # BlogPost, Paragraph, Idea
        ├── serializers.py  # DRF serializers
        ├── views.py        # API viewsets
        ├── urls.py         # API routes
        ├── admin.py        # Django admin config
        └── ocr_service.py  # OCR logic
```

## Troubleshooting

### OCR Fails
- Verify `GEMINI_API_KEY` is set correctly
- Check image format (JPEG, PNG, WEBP)
- Ensure image size < 10MB

### CORS Errors
- Verify `CORS_ALLOWED_ORIGINS` includes React dev server URL
- Check `corsheaders` is in `INSTALLED_APPS`
- Ensure middleware order is correct

### Image Upload Fails
- Check media directory permissions: `chmod 755 media/`
- Verify `MEDIA_ROOT` and `MEDIA_URL` settings
- For S3, check AWS credentials and bucket permissions

## License

MIT

## Support

For issues, contact the development team or open an issue on GitHub.
