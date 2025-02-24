<template>
  <div id="app">
    <b-navbar variant="dark" type="dark" class="mb-0">
      <b-container>
        <b-navbar-brand class="py-3">
          CloudProxy
        </b-navbar-brand>
        <b-navbar-nav class="ml-auto">
          <b-nav-item href="/docs" target="_blank" class="mr-3 text-white">
            <b-icon icon="file-text" class="mr-1"></b-icon>
            API Docs
          </b-nav-item>
          <b-button @click="reloadPage" variant="link" class="refresh-btn text-white">
            <b-icon icon="arrow-clockwise"></b-icon> Refresh
          </b-button>
        </b-navbar-nav>
      </b-container>
    </b-navbar>

    <div class="header-extension py-4 mb-4">
      <b-container>
        <h1 class="text-white mb-0">Proxy Management</h1>
      </b-container>
    </div>

    <b-container>
      <b-card no-body class="main-card">
        <b-card-body class="p-0">
          <ListProxies />
        </b-card-body>
      </b-card>
    </b-container>
  </div>
</template>

<script>
import ListProxies from "./components/ListProxies.vue";

export default {
  name: "App",
  components: {
    ListProxies,
  },
  methods: {
    reloadPage() {
      window.location.reload();
    },
  },
};
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;500&display=swap');

:root {
  --primary-purple: #6b46c1;
  --primary-purple-dark: #553c9a;
  --primary-purple-light: #9f7aea;
  --background-gray: #f7fafc;
  --text-dark: #1a202c;
  --text-gray: #4a5568;
  --border-color: #e2e8f0;
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
  background-color: var(--primary-purple);
  box-shadow: none;
  padding: 0;
}

.header-extension {
  background-color: var(--primary-purple);
  margin-top: -1px;
}

.navbar-brand {
  font-family: var(--font-family);
  font-weight: 700;
  font-size: 1.5rem;
  letter-spacing: -0.5px;
}

h1 {
  font-family: var(--font-family);
  font-weight: 700;
  font-size: 2rem;
  letter-spacing: -0.5px;
}

.refresh-btn {
  font-family: var(--font-family);
  font-weight: 500;
  padding: 0.5rem 1rem;
  transition: opacity 0.2s ease;
}

.refresh-btn:hover {
  opacity: 0.9;
  transform: none;
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
