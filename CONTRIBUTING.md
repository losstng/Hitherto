# Contributing to Hitherto

This guide captures the conventions used throughout the project so new contributors and co-authoring LLMs can work consistently.

## Global Philosophy

- **Clean code** – keep functions small and focused.
- **SOLID principles** – design modules with clear responsibilities and dependency inversion.
- **LLM co-authoring** – when prompting an LLM, provide the relevant context, expected output shape, and review the result before committing.

```text
Prompt: "Add a route that returns the current time as RFC3339."
Expected output: "`/time` router returning `ApiResponse[str]`"
```

## Backend (Python/FastAPI)

### Formatting

- Use [`black`](https://black.readthedocs.io/) and [`isort`](https://pycqa.github.io/isort/) before committing.

```bash
black backend
isort backend
```

### Docstrings

- Write docstrings in the Google style.

```python
def fetch_user(id: int) -> User:
    """Retrieve a user from the database.

    Args:
        id: Primary key of the user.

    Returns:
        The matching user or raises `HTTPException` if not found.
    """
```

### API conventions

- FastAPI routers reside in `backend/routers` and return `ApiResponse` objects.

```python
@router.get("/items/{item_id}")
async def get_item(item_id: int, db: Session = Depends(get_db)) -> ApiResponse[ItemOut]:
    item = repo.get(item_id, db)
    return ApiResponse.success(item)
```

## Frontend (Next.js/React)

### Folder structure and naming

- Components live in `src/components`, hooks in `src/hooks`, and utilities in `src/lib`.
- Each folder exposes an `index.ts` that re-exports public modules. Import from the folder root:

```tsx
import { Sidebar, ChatPanel } from "@/components";
import { useFilters } from "@/hooks";
```

### State management

- Server state uses [TanStack Query](https://tanstack.com/query); local UI state uses React context or `useState`.

### Styling

- Tailwind CSS is the default. Compose classes and avoid inline styles.

```tsx
<button className="px-3 py-1 bg-blue-600 text-white rounded">Send</button>
```

## LLM Prompting Rules

- Begin prompts with a short system message outlining constraints.
- Specify the expected return type or interface.

```text
System: "You are a helpful code generator. Return only valid TypeScript."
User: "Create a `useCounter` hook that increments and decrements." 
```

## Testing

- Run Python tests and frontend linting before opening a pull request.

```bash
pytest -q
cd frontend && npm run lint
```

