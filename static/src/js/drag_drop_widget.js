/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class DragDropFileWidget extends Component {
    setup() {
        this.state = useState({
            isDragging: false,
            files: [],
        });
        this.dropZoneRef = useRef("dropZone");
        this.fileInputRef = useRef("fileInput");
        
        onMounted(() => {
            this.setupDragAndDrop();
        });
        
        onWillUnmount(() => {
            this.cleanupDragAndDrop();
        });
    }

    setupDragAndDrop() {
        const dropZone = this.dropZoneRef.el;
        if (!dropZone) return;

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                this.state.isDragging = true;
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                this.state.isDragging = false;
            }, false);
        });

        // Handle dropped files
        dropZone.addEventListener('drop', (e) => {
            this.handleDrop(e);
        }, false);
    }

    cleanupDragAndDrop() {
        const dropZone = this.dropZoneRef.el;
        if (!dropZone) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.removeEventListener(eventName, this.preventDefaults, false);
            document.body.removeEventListener(eventName, this.preventDefaults, false);
        });
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    async handleDrop(e) {
        const files = Array.from(e.dataTransfer.files);
        await this.processFiles(files);
    }

    async handleFileSelect(e) {
        const files = Array.from(e.target.files);
        await this.processFiles(files);
        // Reset input so same file can be selected again
        e.target.value = '';
    }

    async processFiles(files) {
        const allowedTypes = [
            'application/pdf',
            'image/jpeg',
            'image/jpg',
            'image/png',
            'image/gif',
            'image/bmp',
            'image/webp'
        ];
        const allowedExtensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'];

        const validFiles = files.filter(file => {
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            return allowedTypes.includes(file.type) || allowedExtensions.includes(ext);
        });

        if (validFiles.length === 0) {
            this.env.services.notification.add(
                'No valid files selected. Please select PDF or image files.',
                { type: 'warning' }
            );
            return;
        }

        if (validFiles.length < files.length) {
            this.env.services.notification.add(
                `${files.length - validFiles.length} file(s) were skipped (invalid format).`,
                { type: 'warning' }
            );
        }

        // Process each file and add to the One2many field
        for (const file of validFiles) {
            await this.addFileToWizard(file);
        }
    }

    async addFileToWizard(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = async (e) => {
                try {
                    const base64Data = e.target.result.split(',')[1]; // Remove data:type;base64, prefix
                    
                    // Get the wizard record
                    const wizardRecord = this.props.record;
                    const fileIdsField = wizardRecord.data.file_ids;
                    
                    // Create new file attachment record
                    const newFileRecord = {
                        wizard_id: wizardRecord.resId,
                        filename: file.name,
                        file_data: base64Data,
                        upload_status: 'pending',
                    };

                    // Add to the One2many field
                    if (fileIdsField) {
                        await fileIdsField.addNewRecord(newFileRecord);
                    } else {
                        // Fallback: use the record's update method
                        const currentFiles = wizardRecord.data.file_ids || [];
                        currentFiles.push(newFileRecord);
                        await wizardRecord.update({ file_ids: currentFiles });
                    }
                    
                    resolve();
                } catch (error) {
                    console.error('Error adding file:', error);
                    reject(error);
                }
            };
            
            reader.onerror = () => {
                reject(new Error('Failed to read file'));
            };
            
            reader.readAsDataURL(file);
        });
    }

    openFileDialog() {
        this.fileInputRef.el?.click();
    }

    removeFile(index) {
        const wizardRecord = this.props.record;
        const fileIdsField = wizardRecord.data.file_ids;
        if (fileIdsField && fileIdsField.records) {
            fileIdsField.records[index]?.delete();
        }
    }
}

DragDropFileWidget.template = "docs2ai_copilot.DragDropFileWidget";
DragDropFileWidget.props = {
    ...standardFieldProps,
};

registry.category("fields").add("drag_drop_files", DragDropFileWidget);

