/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { Docs2AIUploadWizardController } from "./drag_drop_files";
import { Docs2AIFileUploader } from "./docs2ai_file_uploader";

// Register the widget here to ensure it's available when the view loads
const docs2aiFileUploader = {
    component: Docs2AIFileUploader,
    extractProps: ({ attrs }) => ({
        readonly: attrs.readonly === "1" || attrs.readonly === "true",
    }),
};

try {
    registry.category("view_widgets").add("docs2ai_file_uploader", docs2aiFileUploader);
    console.log("[Docs2AI] Widget registered in docs2ai_upload_wizard_view.js");
} catch (error) {
    console.error("[Docs2AI] Failed to register widget in docs2ai_upload_wizard_view.js:", error);
}

// Patch the form view to use our custom controller for docs2ai.upload.wizard model
const originalProps = formView.props;
formView.props = (genericProps, view) => {
    const props = originalProps(genericProps, view);
    // Use our custom controller for docs2ai.upload.wizard model
    if (genericProps.resModel === 'docs2ai.upload.wizard') {
        props.Controller = Docs2AIUploadWizardController;
    }
    return props;
};

