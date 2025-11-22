/** @odoo-module **/

// Simple script that runs on document ready to handle file input
(function() {
    'use strict';
    
    function setupFileInput() {
        const fileInput = document.getElementById('docs2ai_file_input');
        const button = document.querySelector('.o_select_files_btn');
        const dropZone = document.querySelector('.o_drag_drop_zone');
        
        if (!fileInput) {
            // Retry after a short delay
            setTimeout(setupFileInput, 500);
            return;
        }
        
        // Ensure file input is enabled and accessible
        fileInput.disabled = false;
        fileInput.removeAttribute('disabled');
        fileInput.style.pointerEvents = 'auto';
        fileInput.tabIndex = -1; // Make it focusable but not in tab order
        
        console.log('Setting up file input handlers', { fileInput, button, dropZone, isLabel: button && button.tagName === 'LABEL' });
        
        // Handle label click - label contains the file input, so clicking label should work natively
        if (button && button.tagName === 'LABEL') {
            console.log('Label found with file input inside');
            // Ensure file input is accessible
            if (fileInput) {
                fileInput.disabled = false;
                fileInput.removeAttribute('disabled');
                // The label wrapping the input should work natively
                console.log('File input is ready, label should work natively');
            }
        } else if (button && button.tagName === 'BUTTON') {
            // Fallback for button - trigger file input click
            const clickHandler = function(e) {
                console.log('Button clicked, triggering file input');
                e.preventDefault();
                e.stopPropagation();
                
                const input = document.getElementById('docs2ai_file_input');
                if (input) {
                    input.disabled = false;
                    input.removeAttribute('disabled');
                    // Direct click should work
                    input.click();
                }
                return false;
            };
            
            button.addEventListener('click', clickHandler, true);
        }
        
        // Handle drop zone click
        if (dropZone) {
            dropZone.addEventListener('click', function(e) {
                if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                    return;
                }
                e.preventDefault();
                fileInput.click();
            });
        }
        
        // Handle drag and drop
        if (dropZone) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(function(eventName) {
                dropZone.addEventListener(eventName, function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                });
            });
            
            dropZone.addEventListener('dragenter dragover', function() {
                dropZone.classList.add('o_dragging');
            });
            
            dropZone.addEventListener('dragleave drop', function() {
                dropZone.classList.remove('o_dragging');
            });
            
            dropZone.addEventListener('drop', function(e) {
                const files = e.dataTransfer.files;
                if (files && files.length > 0) {
                    console.log('Files dropped:', files.length);
                    // Trigger change event on file input
                    const dataTransfer = new DataTransfer();
                    Array.from(files).forEach(file => dataTransfer.items.add(file));
                    fileInput.files = dataTransfer.files;
                    fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        }
        
        // Handle file selection
        fileInput.addEventListener('change', function(e) {
            console.log('File input changed', e.target.files);
            const files = e.target.files;
            if (files && files.length > 0) {
                // Trigger a custom event that the controller can listen to
                const event = new CustomEvent('docs2ai:files-selected', {
                    detail: { files: Array.from(files) },
                    bubbles: true
                });
                document.dispatchEvent(event);
            }
        });
    }
    
    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupFileInput);
    } else {
        setupFileInput();
    }
    
    // Also run when the wizard opens (for dialogs)
    function setupObserver() {
        if (!document.body) {
            setTimeout(setupObserver, 100);
            return;
        }
        
        const observer = new MutationObserver(function(mutations) {
            const fileInput = document.getElementById('docs2ai_file_input');
            if (fileInput && !fileInput.hasAttribute('data-handler-attached')) {
                fileInput.setAttribute('data-handler-attached', 'true');
                setupFileInput();
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    setupObserver();
})();

