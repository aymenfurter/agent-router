# UI Linting and Code Quality

This project includes comprehensive linting and code formatting tools for the UI codebase.

## Tools Configured

- **ESLint** - JavaScript/TypeScript linting with React-specific rules
- **Prettier** - Code formatting
- **TypeScript** - Static type checking
- **Vitest** - Unit testing framework for JavaScript/TypeScript

## Available Scripts

- `npm run lint` - Run ESLint to check for code issues
- `npm run lint:fix` - Run ESLint and automatically fix fixable issues
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check if code is properly formatted
- `npm run type-check` - Run TypeScript type checking
- `npm run test` - Run tests in watch mode
- `npm run test:run` - Run tests once
- `npm run test:ui` - Run tests with UI
- `npm run test:coverage` - Run tests with coverage report
- `npm run check-all` - Run all checks (type-check, lint, format:check, test:run)

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
✅ All tests pass

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
- `vitest.config.ts` - Vitest testing configuration

## Testing

The project uses **Vitest** for unit testing, which is a fast testing framework built specifically for Vite projects.

### Running Tests

```bash
cd ui
npm run test        # Run tests in watch mode
npm run test:run    # Run tests once
npm run test:ui     # Run tests with browser UI
```

### Writing Tests

Tests should be placed in the same directory as the component they test, with a `.test.tsx` extension. Example:

```typescript
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import MyComponent from './MyComponent';

describe('MyComponent', () => {
  it('renders without crashing', () => {
    render(<MyComponent />);
    expect(document.body).toBeInTheDocument();
  });
});
```

The test setup includes:

- `@testing-library/react` for component testing utilities
- `@testing-library/jest-dom` for additional DOM matchers
- `jsdom` environment for DOM simulation
