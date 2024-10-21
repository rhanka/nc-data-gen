<script>
    import { createEventDispatcher } from 'svelte';
  
    export let nonConformities = [];
  
    const dispatch = createEventDispatcher();
    let searchQuery = '';
  
    function selectItem(item) {
      dispatch('select', { item });
    }
  
    // Filter items based on the search
    $: filteredItems = nonConformities.filter(item => {
      const query = searchQuery.toLowerCase();
      return (
        item['Ticket ID'].toLowerCase().includes(query) ||
        item['Category'].toLowerCase().includes(query) ||
        item['Initial Description'].toLowerCase().includes(query) // Added description to the search
      );
    });
  </script>
  
  <div>
    <label for="search">Search</label>
    <input
      id="search"
      type="text"
      bind:value={searchQuery}
      placeholder="Search by ID, category, or description"
      style="margin-bottom: 1rem; padding: 0.5rem; width: 100%;"
    />
  </div>
  
  <ul style="list-style-type: none; padding: 0;">
    {#each filteredItems as item, index}
      <li style="padding: 0; border-bottom: 1px solid #ccc; list-style-type: none;">
        <button 
          type="button" 
          on:click={() => selectItem(item)} 
          on:keypress={(e) => e.key === 'Enter' && selectItem(item)} 
          style="cursor: pointer; padding: 8px; width: 100%; text-align: left; border: none; background: none;">
          <strong>{item['Ticket ID']} - {item['Category']}</strong>
          <p>{item['Initial Description'].slice(0, 100)}...</p>
        </button>
      </li>
    {/each}
  </ul>
  
  <style>
    li:hover {
      background-color: #f0f0f0;
    }
  </style>