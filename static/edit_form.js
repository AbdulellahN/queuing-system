function getTemplates() {
    const language = document.getElementById('language').value;
    const templateSelect = document.getElementById('template_id');
    templateSelect.innerHTML = '';  // Clear existing options
  
    // Retrieve template paths from the session
    const templatePaths = {{ session['template_paths'] | tojson }};
  
    // Check if the selected language exists in templatePaths
    if (templatePaths.hasOwnProperty(language)) {
      // Retrieve template IDs based on the selected language
      const templateIDs = Object.keys(templatePaths[language]);
  
      templateIDs.forEach(templateID => {
        const option = document.createElement('option');
        option.value = templateID;
        option.textContent = templateID;  // Use the template ID as the option text
        templateSelect.appendChild(option);
      });
    } else {
      // Add a default option for when the selected language has no templates
      const defaultOption = document.createElement('option');
      defaultOption.value = '';
      defaultOption.textContent = 'No templates available';
      templateSelect.appendChild(defaultOption);
    }
  }
  
  // Call the getTemplates function when the page loads
  window.addEventListener('DOMContentLoaded', getTemplates);
  
  // Call the getTemplates function when the language is changed
  document.getElementById('language').addEventListener('change', getTemplates);
  
  function goBack() {
    window.history.back();
  }