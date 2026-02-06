/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { Docs2AIUploadWizardController } from "./drag_drop_files";
// Import the widget to ensure it's loaded and registered
import { Docs2AIFileUploader } from "./docs2ai_file_uploader";

// Verify widget is registered, and register it if it's not (fallback)
const viewWidgetsRegistry = registry.category("view_widgets");
if (!viewWidgetsRegistry.contains("docs2ai_file_uploader")) {
    console.warn("[Docs2AI] Widget 'docs2ai_file_uploader' not found in registry. Registering as fallback...");
    // Fallback registration
    const docs2aiFileUploader = {
        component: Docs2AIFileUploader,
        extractProps: ({ attrs }) => ({
            readonly: attrs.readonly === "1" || attrs.readonly === "true",
        }),
    };
    viewWidgetsRegistry.add("docs2ai_file_uploader", docs2aiFileUploader);
    console.log("[Docs2AI] Widget 'docs2ai_file_uploader' registered via fallback");
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

