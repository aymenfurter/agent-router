# UI Linting and Code Quality

This project includes comprehensive linting and code formatting tools for the UI codebase.

## Tools Configured

- **ESLint** - JavaScript/TypeScript linting with React-specific rules
- **Prettier** - Code formatting
- **TypeScript** - Static type checking

## Available Scripts

- `npm run lint` - Run ESLint to check for code issues
- `npm run lint:fix` - Run ESLint and automatically fix fixable issues
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check if code is properly formatted
- `npm run type-check` - Run TypeScript type checking
- `npm run check-all` - Run all checks (type-check, lint, format:check)

## Pre-commit Workflow

Before committing code, run:

```bash
cd ui
npm run check-all
```

This will verify:
✅ TypeScript types are correct  
✅ No linting errors exist
✅ Code is properly formatted

## CI/CD

The GitHub Actions workflow `.github/workflows/ui-lint.yml` automatically runs these checks on:

- Push to main/develop branches (when UI files change)
- Pull requests to main/develop branches (when UI files change)
- Manual workflow dispatch

## Configuration Files

- `eslint.config.js` - ESLint configuration (flat config format for v9)
- `.prettierrc` - Prettier configuration
- `.prettierignore` - Files to ignore for formatting
- `tsconfig.json` - TypeScript configuration
