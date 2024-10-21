<script>
    import { createEventDispatcher } from 'svelte';
    import { marked } from 'marked'; // Import the marked library
  
    export let selectedItem;
    const dispatch = createEventDispatcher();
  
    function closeDetail() {
      dispatch('closeDetail');
    }
  
    // Directive to inject HTML
    function html(node, htmlContent) {
      node.innerHTML = htmlContent;
  
      return {
        update(newHtml) {
          node.innerHTML = newHtml;
        }
      };
    }
  </script>
  
  <div style="margin-top: 1rem; border: 1px solid #ccc; border-radius: 8px; overflow: hidden;">
    <div style="padding: 16px; background-color: #f9f9f9;">
      <h2>{selectedItem['Ticket ID']} - {selectedItem['Category']}</h2>
      <button on:click={closeDetail} style="padding: 0.5rem 1rem; background-color: #6200ee; color: white; border: none; border-radius: 4px; cursor: pointer;">
        Back to List
      </button>
      <p><strong>Open Date:</strong> {selectedItem['Open Date']}</p>
      <p><strong>Initial Description:</strong></p>
      <div style="margin-bottom: 1rem;">
        {@html marked(selectedItem['Initial Description'])}
      </div>
      <h3>Status History:</h3>
      <ul style="list-style-type: none; padding: 0;">
        {#each selectedItem['Status History'] as status}
          <li style="padding: 8px; border-bottom: 1px solid #ccc;">
            <strong>{status.Status} - {status.Date}</strong>
            <div>
              {@html marked(status.Comment)}
            </div>
          </li>
        {/each}
      </ul>
    </div>
    <div style="padding: 16px; text-align: right; background-color: #f9f9f9;">
      <button on:click={closeDetail} style="padding: 0.5rem 1rem; background-color: #6200ee; color: white; border: none; border-radius: 4px; cursor: pointer;">
        Back to List
      </button>
    </div>
  </div>
  
  <style>
    li:hover {
      background-color: #f0f0f0;
    }
  </style>