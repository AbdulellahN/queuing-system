function editTemplate() {
    const title = document.getElementById('subject').value;
    const paragraph = document.getElementById('content').value;
    const footer = document.getElementById('footer').value;
    const language = document.querySelector('input[name="language"]').value;
    const templateId = document.querySelector('input[name="template_id"]').value;
  
    // Prepare data to be sent to the server
    const formData = new FormData();
    formData.append('language', language);
    formData.append('template_id', templateId);
    formData.append('subject', title);
    formData.append('content', paragraph);
    formData.append('footer', footer);
  
    // Send the updated content to the server
    fetch('/edit_email_template', {
      method: 'POST',
      body: formData
    })
      .then(response => {
        if (response.ok) {
          // Reload the page after successfully saving the template
          window.location.reload();
        } else {
          throw new Error('Network response was not ok.');
        }
      })
      .catch(error => {
        // Handle errors
        console.error('Error:', error);
        alert('An error occurred while updating the template.');
      });
  }