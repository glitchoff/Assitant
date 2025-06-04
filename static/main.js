document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('uploadForm');
    const messageDiv = document.getElementById('message');
    const fileInput = document.querySelector('input[type="file"]');

    form.addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent default form submission
        
        if (!fileInput.files.length) {
            showMessage('Please select a file first', 'error');
            return;
        }

        const formData = new FormData(form);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showMessage('File uploaded successfully!', 'success');
                form.reset();
            } else {
                throw new Error(data.detail || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            showMessage(`Error: ${error.message}`, 'error');
        }
    });

    function showMessage(message, type) {
        messageDiv.textContent = message;
        messageDiv.className = `text-${type === 'error' ? 'red' : 'green'}-500 mt-4 text-center`;
        
        // Clear message after 5 seconds
        setTimeout(() => {
            messageDiv.textContent = '';
        }, 4000);
    }
});
