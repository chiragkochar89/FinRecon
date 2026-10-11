import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  Landmark,
  User,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  ShieldCheck,
  Shield
} from 'lucide-react';
import './LoginPage.css';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please provide both username and password.');
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      await login(username.trim(), password);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFillDemo = (user: string, pass: string) => {
    setUsername(user);
    setPassword(pass);
    setError(null);
  };

  return (
    <div className="login-page-wrapper">
      <div className="login-container">
        {/* ===================================================================
         * LEFT BRANDING PANEL
         * =================================================================== */}
        <div className="login-left-panel">
          <div className="login-brand-header">
            <div className="login-brand-icon">
              <Landmark size={28} color="#FFFFFF" strokeWidth={2.2} />
            </div>
            <div className="login-brand-titles">
              <h1 className="login-brand-title">FinRecon</h1>
              <span className="login-brand-subtitle">Financial Operations Platform</span>
            </div>
          </div>

          <h2 className="login-hero-headline">
            Reconcile with
            <span className="highlight">confidence.</span>
          </h2>

          <p className="login-hero-subtitle">
            Secure access to your reconciliation workspace.
          </p>

          <div className="login-pill-badge">
            <span className="login-pill-dot" />
            <span className="login-pill-text">LOCAL DEMO • ACADEMIC SIMULATION</span>
          </div>

          {/* Isometric Financial Ledger Artwork */}
          <div className="login-isometric-graphic" aria-hidden="true">
            <svg viewBox="0 0 440 220" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full">
              <defs>
                <linearGradient id="panelGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#1E40AF" stopOpacity="0.45" />
                  <stop offset="100%" stopColor="#0F172A" stopOpacity="0.8" />
                </linearGradient>
                <linearGradient id="panelGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#2563EB" stopOpacity="0.35" />
                  <stop offset="100%" stopColor="#1E3A8A" stopOpacity="0.6" />
                </linearGradient>
                <linearGradient id="barGlow" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#60A5FA" />
                  <stop offset="100%" stopColor="#2563EB" />
                </linearGradient>
                <linearGradient id="lineGlow" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.2" />
                  <stop offset="50%" stopColor="#60A5FA" />
                  <stop offset="100%" stopColor="#93C5FD" stopOpacity="0.4" />
                </linearGradient>
                <filter id="glowEffect" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="4" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {/* Isometric Grid Lines */}
              <path d="M40 180 L220 70 L400 180" stroke="rgba(59, 130, 246, 0.15)" strokeWidth="1" strokeDasharray="4 4" />
              <path d="M80 190 L260 80 L380 155" stroke="rgba(59, 130, 246, 0.1)" strokeWidth="1" />
              <path d="M120 205 L300 95 L420 170" stroke="rgba(59, 130, 246, 0.1)" strokeWidth="1" />

              {/* Main Floating Ledger Card */}
              <g transform="translate(10, 0)">
                <polygon
                  points="50,150 190,70 330,150 190,230"
                  fill="url(#panelGrad1)"
                  stroke="rgba(96, 165, 250, 0.5)"
                  strokeWidth="1.5"
                />

                {/* Ledger Horizontal Rows in Perspective */}
                <line x1="100" y1="125" x2="240" y2="205" stroke="rgba(96, 165, 250, 0.2)" strokeWidth="1" />
                <line x1="130" y1="110" x2="270" y2="190" stroke="rgba(96, 165, 250, 0.2)" strokeWidth="1" />

                {/* Isometric Data Bars */}
                {/* Bar 1 */}
                <polygon points="120,135 132,128 132,100 120,107" fill="url(#barGlow)" opacity="0.9" />
                <polygon points="132,128 144,135 144,107 132,100" fill="#1D4ED8" opacity="0.9" />
                <polygon points="120,107 132,100 144,107 132,114" fill="#93C5FD" />

                {/* Bar 2 */}
                <polygon points="150,152 162,145 162,85 150,92" fill="url(#barGlow)" opacity="0.95" />
                <polygon points="162,145 174,152 174,92 162,85" fill="#1D4ED8" opacity="0.95" />
                <polygon points="150,92 162,85 174,92 162,99" fill="#BFDBFE" />

                {/* Bar 3 */}
                <polygon points="180,170 192,163 192,115 180,122" fill="url(#barGlow)" opacity="0.85" />
                <polygon points="192,163 204,170 204,122 192,115" fill="#1D4ED8" opacity="0.85" />
                <polygon points="180,122 192,115 204,122 192,129" fill="#93C5FD" />

                {/* Trending Path in Perspective */}
                <path
                  d="M90,140 Q 140,110 170,125 T 260,140"
                  stroke="url(#lineGlow)"
                  strokeWidth="2.5"
                  fill="none"
                  filter="url(#glowEffect)"
                />

                {/* Glowing Target Nodes */}
                <circle cx="90" cy="140" r="3.5" fill="#60A5FA" />
                <circle cx="170" cy="125" r="4" fill="#38BDF8" filter="url(#glowEffect)" />
                <circle cx="260" cy="140" r="3.5" fill="#60A5FA" />
              </g>

              {/* Secondary Floating Secondary Glass Card (Offset Behind) */}
              <polygon
                points="180,75 280,20 380,75 280,130"
                fill="url(#panelGrad2)"
                stroke="rgba(147, 197, 253, 0.4)"
                strokeWidth="1.2"
                opacity="0.8"
              />
              <line x1="220" y1="55" x2="320" y2="110" stroke="rgba(147, 197, 253, 0.25)" strokeWidth="1" />
              <line x1="245" y1="42" x2="345" y2="97" stroke="rgba(147, 197, 253, 0.25)" strokeWidth="1" />
            </svg>
          </div>
        </div>

        {/* ===================================================================
         * RIGHT LOGIN CARD PANEL
         * =================================================================== */}
        <div className="login-right-panel">
          <div className="login-card">
            <h3 className="login-card-title">Welcome back</h3>
            <p className="login-card-subtitle">Sign in to access your workspace.</p>

            {error && (
              <div className="login-alert-error" role="alert">
                <AlertCircle size={18} className="login-alert-icon" />
                <div>
                  <strong>Authentication Failed: </strong>
                  {error}
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="login-form">
              {/* Username Input */}
              <div className="login-field-group">
                <label htmlFor="login-username" className="login-field-label">
                  Username or Operator ID
                </label>
                <div className="login-input-wrapper">
                  <div className="login-input-icon-left">
                    <User size={18} />
                  </div>
                  <input
                    id="login-username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter your username"
                    required
                    autoFocus
                    className="login-input"
                  />
                </div>
              </div>

              {/* Password Input */}
              <div className="login-field-group">
                <label htmlFor="login-password" className="login-field-label">
                  Password
                </label>
                <div className="login-input-wrapper">
                  <div className="login-input-icon-left">
                    <Lock size={18} />
                  </div>
                  <input
                    id="login-password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    required
                    className="login-input has-right-button"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="login-input-btn-right"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="login-submit-button"
              >
                {isLoading ? (
                  <>
                    <span className="login-button-spinner" />
                    <span>Signing in securely...</span>
                  </>
                ) : (
                  <>
                    <span>Sign in securely</span>
                    <ArrowRight size={18} />
                  </>
                )}
              </button>
            </form>

            {/* Demo Accounts Divider */}
            <div className="login-demo-divider">
              <span>Demo accounts</span>
            </div>

            {/* Demo Account Cards Grid */}
            <div className="login-demo-grid">
              {/* USER Demo Card */}
              <button
                type="button"
                onClick={() => handleFillDemo('finrecon_user', 'FinReconUser2026!')}
                className="login-demo-card user"
                title="Click to fill USER demo credentials"
              >
                <div className="login-demo-avatar">
                  <User size={18} />
                </div>
                <div className="login-demo-info">
                  <span className="login-demo-title">USER</span>
                  <span className="login-demo-desc">Reconciliation and exception review</span>
                </div>
              </button>

              {/* SUPERVISOR Demo Card */}
              <button
                type="button"
                onClick={() => handleFillDemo('finrecon_supervisor', 'FinReconSuper2026!')}
                className="login-demo-card supervisor"
                title="Click to fill SUPERVISOR demo credentials"
              >
                <div className="login-demo-avatar">
                  <ShieldCheck size={18} />
                </div>
                <div className="login-demo-info">
                  <span className="login-demo-title">SUPERVISOR</span>
                  <span className="login-demo-desc">Oversight, resolution and reporting</span>
                </div>
              </button>
            </div>

            {/* Security Footer */}
            <div className="login-security-footer">
              <Shield size={14} />
              <span>Protected sessions • Role-based access • Audit logging</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
