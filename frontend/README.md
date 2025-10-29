# Frontend - React + Material-UI

This is the frontend application built with React, TypeScript, and Material-UI.

## Features

- 🎨 Modern UI with Material-UI components
- 📱 Responsive design for desktop and mobile
- 🔧 TypeScript for type safety
- 🚀 Fast development with Create React App
- 🌐 API integration with Axios
- 🧭 Client-side routing with React Router

## Getting Started

### Prerequisites

- Node.js 18 or higher
- npm or yarn package manager

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The application will open at [http://localhost:3000](http://localhost:3000).

### Available Scripts

```bash
# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build

# Eject from Create React App (not recommended)
npm run eject
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   └── Layout.tsx      # Main application layout
├── pages/              # Page components
│   ├── HomePage.tsx    # Landing page
│   └── GraphPage.tsx   # Graph processing interface
├── services/           # API services
│   ├── api.ts         # Axios configuration
│   └── graphService.ts # Graph API calls
├── hooks/             # Custom React hooks
├── types/             # TypeScript type definitions
├── utils/             # Utility functions
├── App.tsx            # Main App component
└── index.tsx          # Application entry point
```

## Components

### Layout Component
- Responsive navigation with drawer for mobile
- Material-UI AppBar and navigation
- Consistent layout across all pages

### HomePage
- Welcome screen with feature cards
- Navigation to different sections
- Overview of application capabilities

### GraphPage
- Input interface for LangGraph processing
- Real-time results display
- Error handling and loading states

## API Integration

The frontend communicates with the backend through:

- `graphService.ts` - Graph processing API calls
- `api.ts` - Axios configuration with interceptors
- Proxy configuration in `package.json` for development

## Styling

- Material-UI theme configuration
- Responsive design principles
- Consistent spacing and typography
- Dark/light theme support ready

## Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

## Development Tips

1. **Hot Reload**: Changes automatically reflect in the browser
2. **TypeScript**: Use proper typing for better development experience
3. **Material-UI**: Leverage the component library for consistent UI
4. **API Integration**: Use the service layer for all API calls

## Building for Production

```bash
npm run build
```

Creates an optimized production build in the `build` folder.

## Testing

```bash
# Run tests in watch mode
npm test

# Run tests with coverage
npm test -- --coverage
```

## Deployment

The built application can be deployed to:
- Netlify
- Vercel
- AWS S3 + CloudFront
- Any static hosting service