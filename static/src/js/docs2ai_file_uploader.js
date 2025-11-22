/** @odoo-module **/

import { Component } from "@odoo/owl";
import { FileUploader } from "@web/views/fields/file_handler";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class Docs2AIFileUploader extends Component {
    static template = "docs2ai_copilot.Docs2AIFileUploader";
    static components = { FileUploader };
    static props = {
        record: { type: Object },
        readonly: { type: Boolean, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.acceptedFileExtensions = ".pdf,.jpg,.jpeg,.png,.gif,.bmp,.webp";
    }

    get wizardId() {
        // Get wizard ID from the record - try multiple ways
        const record = this.props.record;
        if (!record) {
            return null;
        }
        
        // Try resId first (for existing records)
        if (record.resId && record.resId > 0) {
            return record.resId;
        }
        
        // Try data.id (for new records that have been saved)
        if (record.data?.id && record.data.id > 0) {
            return record.data.id;
        }
        
        // For new records, we might need to save first
        // But let's try to get the temporary ID
        if (record.resId !== false && record.resId !== undefined) {
            return record.resId;
        }
        
        return null;
    }

    async onFileUploaded(fileData) {
        const { name, data } = fileData;
        
        let wizardId = this.wizardId;
        
        // If no ID yet, try to save the wizard first
        if (!wizardId || wizardId <= 0) {
            try {
                // Save the wizard record to get an ID
                const saved = await this.props.record.save({ reload: false });
                if (saved) {
                    wizardId = this.props.record.resId;
                }
            } catch (error) {
                console.error("Error saving wizard:", error);
            }
        }
        
        if (!wizardId || wizardId <= 0) {
            this.notification.add(
                _t("Please wait for the wizard to initialize."),
                { type: "warning" }
            );
            return;
        }

        try {
            // Create file attachment record
            await this.orm.create("docs2ai.file.attachment", [{
                wizard_id: wizardId,
                filename: name,
                file_data: data,
                upload_status: "pending",
            }]);

            // Reload the record to show new files
            await this.props.record.load();

            this.notification.add(
                _t("File '%s' added successfully.", name),
                { type: "success" }
            );
        } catch (error) {
            this.notification.add(
                _t("Error adding file: %s", error.message || error),
                { type: "danger" }
            );
        }
    }
}

export const docs2aiFileUploader = {
    component: Docs2AIFileUploader,
};

registry.category("view_widgets").add("docs2ai_file_uploader", docs2aiFileUploader);

