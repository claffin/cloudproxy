<template>
  <div id="app">
    <nav class="navbar navbar-dark mb-0">
      <div class="container">
        <span class="navbar-brand py-3 text-dark">
          CloudProxy
        </span>
        <div class="navbar-nav ms-auto d-flex flex-row">
          <a
            class="nav-link me-3 text-dark d-flex align-items-center"
            href="/docs"
            target="_blank"
          >
            <i class="bi bi-file-text me-1" />
            <span>API Docs</span>
          </a>
          <button
            class="btn btn-link nav-link text-dark d-flex align-items-center"
            type="button"
            @click="reloadPage"
          >
            <i class="bi bi-arrow-clockwise me-1" />
            <span>Refresh</span>
          </button>
        </div>
      </div>
    </nav>

    <div class="header-extension py-4 mb-4">
      <div class="container">
        <h1 class="text-white mb-0">
          Proxy Management
        </h1>
      </div>
    </div>

    <div class="container">
      <RollingConfig />
      <div class="card main-card">
        <div class="card-body p-0">
          <ListProxies />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ListProxies from "./components/ListProxies.vue";
import RollingConfig from "./components/RollingConfig.vue";

export default {
  name: "App",
  components: {
    ListProxies,
    RollingConfig,
  },
  setup() {
    const reloadPage = () => {
      window.location.reload();
    };

    return {
      reloadPage
    };
  }
};
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;500&display=swap');
@import url('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css');

:root {
  --primary-purple: #6b46c1;
  --primary-purple-dark: #553c9a;
  --primary-purple-light: #9f7aea;
  --background-gray: #f7fafc;
  --text-dark: #1a202c;
  --text-gray: #4a5568;
  --border-color: #e2e8f0;
  --navbar-gray: #2d3748;
  --font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
}

#app {
  font-family: var(--font-family);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text-dark);
  min-height: 100vh;
  background-color: var(--background-gray);
  letter-spacing: 0.2px;
}

.navbar {
  background-color: var(--navbar-gray);
  box-shadow: none;
  padding: 0;
  border-bottom: none;
}

.navbar .nav-link {
  color: #e2e8f0 !important;
  opacity: 0.9;
  transition: opacity 0.2s ease;
  text-decoration: none;
}

.navbar .nav-link:hover {
  opacity: 1;
  color: white !important;
}

.header-extension {
  background-color: var(--primary-purple);
  margin-top: 0;
}

.navbar-brand {
  font-family: var(--font-family);
  font-weight: 700;
  font-size: 1.5rem;
  letter-spacing: -0.5px;
  color: white !important;
}

h1 {
  font-family: var(--font-family);
  font-weight: 700;
  font-size: 2rem;
  letter-spacing: -0.5px;
}

.btn-link {
  text-decoration: none;
  padding: 0.5rem 1rem;
  transition: opacity 0.2s ease;
}

.btn-link:hover {
  opacity: 0.9;
  color: var(--text-dark) !important;
}

.main-card {
  border-radius: 8px;
  border: 1px solid var(--border-color);
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  background-color: white;
}

/* Bootstrap overrides */
.btn {
  font-family: var(--font-family);
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  letter-spacing: 0.3px;
}

.btn-primary {
  background-color: var(--primary-purple);
  border-color: var(--primary-purple);
}

.btn-primary:hover {
  background-color: var(--primary-purple-dark);
  border-color: var(--primary-purple-dark);
}

.btn-outline-primary {
  color: var(--primary-purple);
  border-color: var(--primary-purple);
}

.btn-outline-primary:hover {
  background-color: var(--primary-purple);
  border-color: var(--primary-purple);
}

.btn-danger {
  background-color: #e53e3e;
  border-color: #e53e3e;
}

.btn-danger:hover {
  background-color: #c53030;
  border-color: #c53030;
}

.form-control:focus {
  border-color: var(--primary-purple-light);
  box-shadow: 0 0 0 1px var(--primary-purple-light);
}

/* Typography overrides */
.form-control,
.custom-select,
.input-group-text {
  font-family: var(--font-family);
}

label {
  font-family: var(--font-family);
  font-weight: 500;
}

small {
  font-family: var(--font-family);
}
</style>
