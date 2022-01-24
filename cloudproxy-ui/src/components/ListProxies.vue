<template>
  <div>
    <div class="mb-4" v-for="(item, key, index) in data" :key="index">
      <b-list-group>
        <div class="d-flex w-100 justify-content-between mb-2">
          <h2>{{ key }}</h2>
          <b-form v-on:click="updateProvider(key, item.scaling.min_scaling)"
            ><label for="sb-inline" class="mr-2"
              >{{ item.ips.length }} ready of</label
            ><b-form-spinbutton
              v-model="item.scaling.min_scaling"
              min="0"
              max="100"
              inline
            ></b-form-spinbutton
          ></b-form>
        </div>
        <b-list-group-item
          href="#"
          class="flex-column align-items-start"
          v-for="ips in item.ips"
          :key="ips"
        >
          <div class="d-flex w-100 justify-content-between">
            <p class="mb-1">{{ ips }}</p>
            <b-button variant="danger" v-if="listremove_data.includes(ips)"
              ><b-spinner small type="grow"></b-spinner> Removing...</b-button
            >
            <b-button
              v-on:click="
                removeProxy(ips);
                makeToast(ips);
              "
              variant="danger"
              v-else
              >Remove</b-button
            >
          </div>
        </b-list-group-item>
        <b-list-group-item
          href="#"
          class="flex-column align-items-start"
          v-if="item.scaling.min_scaling > item.ips.length"
        >
          <b-progress
            :max="item.scaling.min_scaling"
            height="3rem"
            show-progress
            animated
            ><b-progress-bar :value="item.ips.length"
              ><span
                ><strong
                  >Deploying: {{ item.ips.length }} /
                  {{ item.scaling.min_scaling }}</strong
                ></span
              ></b-progress-bar
            ></b-progress
          >
        </b-list-group-item>
      </b-list-group>
    </div>
  </div>
</template>

<script>
export default {
  name: "ListProxies.vue",
  mounted: function () {
    window.setInterval(() => {
      this.getName(), this.listremoveProxy();
    }, 3000);
  },
  data() {
    return {
      data: {},
      listremove_data: {},
      toastCount: 0,
    };
  },
  beforeMount() {
    this.getName();
    this.listremoveProxy();
  },
  methods: {
    async getName() {
      const res = await fetch("/providers");
      const data = await res.json();
      this.data = data;
    },
    async removeProxy(proxy) {
      const remove_res = await fetch(
        "/destroy?ip_address=" + proxy,
        { method: "DELETE", body: JSON.stringify(proxy) }
      );
      const remove_data = await remove_res.json();
      this.remove_data = remove_data;
    },
    async listremoveProxy() {
      const listremove_res = await fetch("/destroy");
      const listremove_data = await listremove_res.json();
      this.listremove_data = listremove_data;
    },
    async updateProvider(provider, min_scaling) {
      const updateProvider_res = await fetch(
        "/providers/" +
          provider +
          "?min_scaling=" +
          min_scaling +
          "&max_scaling=" +
          min_scaling,
        { method: "PATCH" }
      );
      const updateProvider_data = await updateProvider_res.json();
      this.updateProvider_data = updateProvider_data;
    },
    makeToast(ips, append = false) {
      this.toastCount++;
      this.$bvToast.toast(`${ips}`, {
        title: "Removing proxy from pool",
        autoHideDelay: 5000,
        appendToast: append,
      });
    },
    reloadPage() {
      window.location.reload();
    },
  },
};
</script>

<style scoped></style>
