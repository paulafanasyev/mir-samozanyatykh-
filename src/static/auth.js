/* Mir Samozanykh legacy-page auth bridge.
 * Access tokens live only in this page's JS memory.
 * Refresh token is an HttpOnly cookie; CSRF token is mirrored in a readable cookie.
 */
(function () {
  let accessToken = null;
  let refreshPromise = null;

  function csrfToken() {
    const part = document.cookie.split('; ').find((x) => x.startsWith('csrf_token='));
    return part ? decodeURIComponent(part.split('=').slice(1).join('=')) : '';
  }

  async function refresh() {
    if (!refreshPromise) {
      refreshPromise = fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-CSRF-Token': csrfToken() }
      }).then(async (response) => {
        if (!response.ok) return null;
        const data = await response.json();
        accessToken = data.access_token || null;
        return accessToken;
      }).catch(() => null).finally(() => { refreshPromise = null; });
    }
    return refreshPromise;
  }

  window.MirAuth = {
    setToken(token) { accessToken = token || null; },
    clear() { accessToken = null; },
    async getToken() {
      if (accessToken) return accessToken;
      return refresh();
    }
  };
})();
