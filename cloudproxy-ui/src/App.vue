<template>
  <b-container>
  <div id="app">
    <b-row>
      <b-col><h1>CloudProxy</h1></b-col>
      <b-col cols="12" class="pt-2" md="auto"><b-button @click="reloadPage" variant="success">Refresh</b-button></b-col>
    </b-row>
    <br>
    <div>
      <b-card no-body>
        <b-tabs card>
          <b-tab title="Proxies" active>
            <ListProxies />
          </b-tab>
        </b-tabs>

      </b-card>
    </div>
  </div>
    </b-container>
</template>

<script>
import ListProxies from './components/ListProxies.vue'

export default {
  name: 'App',
  components: {
    ListProxies,
  },
  methods: {
    reloadPage() {
      window.location.reload();
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
