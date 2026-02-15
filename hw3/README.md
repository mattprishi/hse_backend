# HW3: Moderation Service with PostgreSQL

## Setup

### 1. Install PostgreSQL

```bash
# macOS
brew install postgresql@14
brew services start postgresql@14

# Create database
createdb moderation
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Run migrations

```bash
# Install pgmigrate
pip install yandex-pgmigrate

# Run migrations
pgmigrate -t latest -c "host=localhost port=5432 dbname=moderation user=postgres password=postgres" migrate
```

Or manually:

```bash
psql -d moderation -f migrations/V01__init_schema.sql
```

### 4. Configure environment

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/moderation"
export MODEL_PATH="model.pkl"
```

### 5. Run application

```bash
python main.py
```

## API Endpoints

### POST /simple_predict

Predicts violations by item_id only.

**Request:**
```json
{
  "item_id": 1
}
```

**Response:**
```json
{
  "is_violation": true,
  "probability": 0.85
}
```

## Run Tests

```bash
pytest tests/ -v
```

## Architecture

- **Repository Pattern**: Separates data access logic
- **Dependency Injection**: Services injected via FastAPI Depends
- **Connection Pooling**: asyncpg pool for efficient DB access
- **Clean separation**: DB ← Repository ← Service ← Router
