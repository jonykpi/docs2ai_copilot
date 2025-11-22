/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class Docs2AIUploadWizardController extends FormController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        // Only setup drag and drop for docs2ai.upload.wizard model
        if (this.props.resModel === 'docs2ai.upload.wizard') {
            onMounted(() => {
                // Setup drag and drop zone
                this._setupDragAndDrop();
            });
            
            // Listen for file added events to reload the form
            this.env.bus.addEventListener("docs2ai:file-added", () => {
                this.model.root.load();
            });
        }
    }

    async onFilesAdded() {
        // Reload the form to show new files
        await this.model.root.load();
    }

    _setupDragAndDrop() {
        // Setup drag and drop for the FileUploader component
        const dropZone = this.el?.querySelector('.o_drag_drop_zone');
        if (!dropZone) {
            setTimeout(() => this._setupDragAndDrop(), 500);
            return;
        }

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach((eventName) => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        dropZone.addEventListener('dragenter', () => dropZone.classList.add('o_dragging'));
        dropZone.addEventListener('dragover', () => dropZone.classList.add('o_dragging'));
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('o_dragging'));
        dropZone.addEventListener('drop', () => dropZone.classList.remove('o_dragging'));

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                // Find the file input in the FileUploader
                const fileInput = dropZone.querySelector('input[type="file"]');
                if (fileInput) {
                    const dataTransfer = new DataTransfer();
                    Array.from(files).forEach(file => dataTransfer.items.add(file));
                    fileInput.files = dataTransfer.files;
                    fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        });
    }

    _setupDragAndDropWithRetry(retries = 5) {
        if (retries <= 0) {
            console.error('Failed to setup drag and drop after multiple attempts');
            return;
        }

        const dropZone = document.querySelector('.o_drag_drop_zone');
        const fileInput = document.getElementById('docs2ai_file_input') || document.querySelector('.o_file_input');
        const button = document.querySelector('.o_select_files_btn') || document.querySelector('.o_drag_drop_zone button');

        if (!dropZone || !fileInput || !button) {
            console.log(`Retrying setup... (${retries} attempts left)`, { dropZone: !!dropZone, fileInput: !!fileInput, button: !!button });
            setTimeout(() => {
                this._setupDragAndDropWithRetry(retries - 1);
            }, 300);
            return;
        }

        console.log('All elements found, setting up handlers');
        this._setupDragAndDropHandlers(dropZone, fileInput, button);
    }

    _setupDragAndDropHandlers(dropZone, fileInput, button) {
        // Remove any existing handlers first
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        const newFileInput = fileInput.cloneNode(true);
        fileInput.parentNode.replaceChild(newFileInput, fileInput);

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach((eventName) => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        // Highlight drop zone
        dropZone.addEventListener('dragenter', () => {
            dropZone.classList.add('o_dragging');
        });
        
        dropZone.addEventListener('dragover', () => {
            dropZone.classList.add('o_dragging');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('o_dragging');
        });
        
        dropZone.addEventListener('drop', () => {
            dropZone.classList.remove('o_dragging');
        });

        // Handle drop
        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                this._processFiles(files);
            }
        });

        // Handle button click - use multiple event types
        const buttonClickHandler = (e) => {
            console.log('Button clicked!', e);
            e.stopPropagation();
            e.preventDefault();
            e.stopImmediatePropagation();
            console.log('Triggering file input click');
            newFileInput.click();
            return false;
        };

        newButton.addEventListener('click', buttonClickHandler, true);
        newButton.addEventListener('mousedown', (e) => {
            e.preventDefault();
            newFileInput.click();
        }, true);
        
        // Also add onclick attribute as fallback
        newButton.setAttribute('onclick', 'document.getElementById("docs2ai_file_input").click(); return false;');

        // Handle click on drop zone (but not button)
        dropZone.addEventListener('click', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                return;
            }
            e.preventDefault();
            e.stopPropagation();
            newFileInput.click();
        });

        // Handle file selection
        const fileChangeHandler = (e) => {
            console.log('File input changed', e.target.files);
            const files = e.target.files;
            if (files && files.length > 0) {
                this._processFiles(files);
                // Reset input after processing
                e.target.value = '';
            }
        };
        newFileInput.addEventListener('change', fileChangeHandler);
        
        // Also listen for custom event from simple handler
        document.addEventListener('docs2ai:files-selected', (e) => {
            console.log('Custom files-selected event received', e.detail.files);
            if (e.detail && e.detail.files) {
                // Convert FileList to array
                const files = e.detail.files;
                this._processFiles(files);
            }
        });
        
        console.log('Drag and drop zone initialized successfully');
    }

    async _processFiles(files) {
        const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'];
        const allowedExtensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'];

        const validFiles = Array.from(files).filter((file) => {
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            return allowedTypes.includes(file.type) || allowedExtensions.includes(ext);
        });

        if (validFiles.length === 0) {
            this.notification.add(
                _t('No valid files selected. Please select PDF or image files.'),
                { type: 'warning' }
            );
            return;
        }

        if (validFiles.length < files.length) {
            this.notification.add(
                _t('%d file(s) were skipped (invalid format).', files.length - validFiles.length),
                { type: 'warning' }
            );
        }

        // Get wizard record ID
        const record = this.model.root;
        const wizardId = record.resId;

        if (!wizardId) {
            this.notification.add(
                _t('Please save the wizard first before adding files.'),
                { type: 'warning' }
            );
            return;
        }

        // Show loading notification
        this.notification.add(
            _t('Adding %d file(s) to list...', validFiles.length),
            { type: 'info' }
        );

        // Process all files and create records
        await this._addFilesToWizard(validFiles, wizardId);
    }

    async _addFilesToWizard(files, wizardId) {
        const filePromises = [];
        const fileDataList = [];

        // Read all files first
        for (const file of files) {
            const promise = new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const base64Data = e.target.result.split(',')[1];
                    fileDataList.push({
                        wizard_id: wizardId,
                        filename: file.name,
                        file_data: base64Data,
                        upload_status: 'pending',
                    });
                    resolve();
                };
                reader.onerror = () => {
                    reject(new Error('Failed to read file: ' + file.name));
                };
                reader.readAsDataURL(file);
            });
            filePromises.push(promise);
        }

        try {
            // Wait for all files to be read
            await Promise.all(filePromises);
            
            if (fileDataList.length === 0) {
                return;
            }

            // Create all file attachment records at once
            await this.orm.create('docs2ai.file.attachment', fileDataList);
            
            // Reload the form to show new files in the list
            await this.model.root.load();
            
            this.notification.add(
                _t('%d file(s) added to list. Click "Upload All Files" to upload them.', files.length),
                { type: 'success' }
            );
        } catch (error) {
            console.error('Error adding files:', error);
            this.notification.add(
                _t('Error adding files: %s', error.message || error),
                { type: 'danger' }
            );
        }
    }
}
