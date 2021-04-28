<template>
  <div>
    {{ data }}
  </div>
</template>

<script>
export default {
  name: "ListProxies.vue",
  data() {
    return {
      data: {},
    }
  },
  beforeMount(){
    this.getLogs();
  },
  methods: {
    async getLogs(){
      const res = await fetch('http://localhost:8000/logs');
      const data = await res.json();
      this.data = data;
    },
  }
}
</script>

<style scoped>

</style>