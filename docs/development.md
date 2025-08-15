# Development Guide

This guide covers local development setup, code style, and best practices for contributing to SportsHunt.

## 🛠️ Local Development Setup

1. Clone the repository and install dependencies (see [Getting Started](./getting-started.md)).
2. Create a `.env` file with development settings.
3. Run the development server:

```bash
python manage.py runserver
```

## 👩‍💻 Code Style & Linting

- Follow [PEP8](https://www.python.org/dev/peps/pep-0008/) for Python code.
- Use `black` for code formatting:
  ```bash
  black .
  ```
- Use `flake8` for linting:
  ```bash
  flake8
  ```

## 🧪 Testing

- See [Testing Guide](./testing.md) for details.

## 📝 Pre-commit Hooks (Recommended)

- Install pre-commit:
  ```bash
  pip install pre-commit
  pre-commit install
  ```
- This will auto-format and lint code before each commit.

## 🤝 Contributing

- Fork the repo and create a feature branch.
- Write clear commit messages.
- Open a pull request with a description of your changes.

## 🔄 Useful Commands

- Run migrations:
  ```bash
  python manage.py migrate
  ```
- Create a superuser:
  ```bash
  python manage.py createsuperuser
  ```
- Run tests:
  ```bash
  python manage.py test
  ```
