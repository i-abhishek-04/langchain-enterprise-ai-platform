import React, { useState } from 'react';
import { loginApi, registerApi } from '../services/apiClient';

export default function AuthScreen({ onAuthenticated }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      const authenticate = isRegistering ? registerApi : loginApi;
      const result = await authenticate({ email, password });
      onAuthenticated(result);
    } catch (requestError) {
      setError(requestError.message || 'Unable to authenticate.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main style={{ flex: 1, display: 'grid', placeItems: 'center', padding: '24px' }}>
      <section className="glass-panel" style={{ width: 'min(100%, 420px)', padding: '28px' }}>
        <h2 style={{ marginBottom: '8px' }}>
          {isRegistering ? 'Create your account' : 'Sign in'}
        </h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
          Sign in to use the document Q&amp;A API and playground.
        </p>
        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '14px' }}>
          <label style={{ display: 'grid', gap: '6px' }}>
            <span>Email</span>
            <input
              className="input-field"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label style={{ display: 'grid', gap: '6px' }}>
            <span>Password</span>
            <input
              className="input-field"
              type="password"
              autoComplete={isRegistering ? 'new-password' : 'current-password'}
              minLength={8}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error && (
            <p role="alert" style={{ color: 'var(--accent-rose)' }}>{error}</p>
          )}
          <button className="btn btn-primary" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Please wait…' : isRegistering ? 'Register' : 'Login'}
          </button>
        </form>
        <button
          className="btn btn-outline"
          type="button"
          onClick={() => {
            setError('');
            setIsRegistering((registering) => !registering);
          }}
          style={{ width: '100%', marginTop: '12px' }}
        >
          {isRegistering ? 'Already have an account? Login' : 'Need an account? Register'}
        </button>
      </section>
    </main>
  );
}
