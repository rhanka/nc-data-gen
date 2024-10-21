<script>
  import NonConformityList from './NonConformityList.svelte';
  import NonConformityDetail from './NonConformityDetail.svelte';
	import { nonConformities } from './non_conformities.js';
		
  let selectedItem = null;
  function handleSelect(event) {
    selectedItem = event.detail.item;
  }

  function closeDetail() {
    selectedItem = null;
  }
</script>

<main>
  {#if selectedItem}
    <NonConformityDetail {selectedItem} on:closeDetail={closeDetail} />
  {:else}
    <NonConformityList {nonConformities} on:select={handleSelect} />
  {/if}
</main>

<style>
  main {
    padding: 1rem;
  }
</style>