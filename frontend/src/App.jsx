import React, { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, useLocation, Navigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { Loader } from 'lucide-react'
import { Toaster } from 'react-hot-toast'
import { ErrorBoundary } from 'react-error-boundary'
import PageTransition from './components/PageTransition'
import ErrorFallback from './components/ErrorFallback'
import PageSkeleton from './components/PageSkeleton'
import RouteGuard from './components/RouteGuard'
import { AuthProvider } from './context/AuthContext'
import MarketingLayout from './components/marketing/MarketingLayout'

/**
 * Retry wrapper for lazy imports — handles "Failed to fetch dynamically imported
 * module" errors caused by stale browser cache serving invalidated chunk hashes.
 * Retries up to 3 times with 1-second backoff, then forces a single page reload
 * so the browser fetches the current index.html with valid chunk filenames.
 */
function lazyWithRetry(importFn, retries = 3, delay = 1000) {
  return lazy(() => {
    const attempt = (retriesLeft) =>
      importFn().catch((err) => {
        if (retriesLeft > 0) {
          return new Promise((resolve) => setTimeout(resolve, delay)).then(() =>
            attempt(retriesLeft - 1)
          );
        }
        // All retries exhausted — likely stale chunk hashes after a rebuild.
        // Force a one-time full page reload so the browser fetches the new
        // index.html with current chunk filenames. A sessionStorage flag
        // prevents infinite reload loops.
        const reloadKey = 'fluxline_chunk_reload';
        if (!sessionStorage.getItem(reloadKey)) {
          sessionStorage.setItem(reloadKey, '1');
          window.location.reload();
          // Return a never-resolving promise so React doesn't render an error
          // while the page is reloading
          return new Promise(() => {});
        }
        // Already reloaded once this session — surface the real error
        sessionStorage.removeItem(reloadKey);
        throw err;
      });
    return attempt(retries);
  });
}

// Lazy Load Pages for Production Performance (Route-level Code Splitting)
const Landing = lazyWithRetry(() => import('./pages/Landing'))
const Pricing = lazyWithRetry(() => import('./pages/Pricing'))
const Docs = lazyWithRetry(() => import('./pages/Docs'))
const Sandbox = lazyWithRetry(() => import('./pages/Sandbox'))
const Architecture = lazyWithRetry(() => import('./pages/Architecture'))
const DashboardLayout = lazyWithRetry(() => import('./pages/DashboardLayout'))
const Dashboard = lazyWithRetry(() => import('./pages/Dashboard'))
const NewMigration = lazyWithRetry(() => import('./pages/NewMigration'))
const MigrationProgress = lazyWithRetry(() => import('./pages/MigrationProgress.jsx'))
const MigrationReport = lazyWithRetry(() => import('./pages/MigrationReport'))
const MigrationHistory = lazyWithRetry(() => import('./pages/MigrationHistory'))
const Demo = lazyWithRetry(() => import('./pages/Demo'))
const Analytics = lazyWithRetry(() => import('./pages/Analytics'))
const SchemaVisualizer = lazyWithRetry(() => import('./pages/SchemaVisualizer'))
const Login = lazyWithRetry(() => import('./pages/Login'))
const Register = lazyWithRetry(() => import('./pages/Register'))
const ChangePassword = lazyWithRetry(() => import('./pages/ChangePassword'))
const ForgotPassword = lazyWithRetry(() => import('./pages/ForgotPassword'))
const UserManagement = lazyWithRetry(() => import('./pages/UserManagement'))
const Schedules = lazyWithRetry(() => import('./pages/Schedules'))
const Webhooks = lazyWithRetry(() => import('./pages/Webhooks'))
const DataMasking = lazyWithRetry(() => import('./pages/DataMasking'))
const MigrationCompare = lazyWithRetry(() => import('./pages/MigrationCompare'))

function AnimatedRoutes() {
  const location = useLocation()
  const pathKey = location.pathname.startsWith('/app') ? '/app' : location.pathname

  return (
    <AnimatePresence mode="wait">
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <Suspense fallback={<PageSkeleton />}>
          <Routes location={location} key={pathKey}>
            {/* Public Marketing Routes wrapped in MarketingLayout */}
            <Route element={<MarketingLayout />}>
              <Route path="/" element={<PageTransition><Landing /></PageTransition>} />
              <Route path="/pricing" element={<PageTransition><Pricing /></PageTransition>} />
              <Route path="/docs" element={<PageTransition><Docs /></PageTransition>} />
              <Route path="/sandbox" element={<PageTransition><Sandbox /></PageTransition>} />
              <Route path="/architecture" element={<PageTransition><Architecture /></PageTransition>} />
            </Route>

            {/* Auth Routes */}
            <Route path="/login" element={<PageTransition><Login /></PageTransition>} />
            <Route path="/register" element={<PageTransition><Register /></PageTransition>} />
            <Route path="/forgot-password" element={<PageTransition><ForgotPassword /></PageTransition>} />
            <Route path="/new-migration" element={<Navigate to="/app/new" replace />} />
            
            {/* Authenticated App Routes */}
            <Route path="/app" element={<RouteGuard><DashboardLayout /></RouteGuard>}>
              <Route index element={<Dashboard />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="schema" element={<SchemaVisualizer />} />
              <Route path="new" element={<NewMigration />} />
              <Route path="progress/:id" element={<MigrationProgress />} />
              <Route path="report/:id" element={<MigrationReport />} />
              <Route path="history" element={<MigrationHistory />} />
              <Route path="schedules" element={<Schedules />} />
              <Route path="webhooks" element={<Webhooks />} />
              <Route path="masking" element={<DataMasking />} />
              <Route path="compare" element={<MigrationCompare />} />
              <Route path="demo" element={<Demo />} />
              <Route path="settings/password" element={<ChangePassword />} />
              <Route path="settings/users" element={<RouteGuard requireRole="Admin"><UserManagement /></RouteGuard>} />
            </Route>
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </AnimatePresence>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster position="top-right" />
        <AnimatedRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
