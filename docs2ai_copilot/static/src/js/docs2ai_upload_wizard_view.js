/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { Docs2AIUploadWizardController } from "./drag_drop_files";
// Import the widget to ensure it's loaded and registered
import "./docs2ai_file_uploader";

// Verify widget is registered (fallback check)
const viewWidgetsRegistry = registry.category("view_widgets");
if (!viewWidgetsRegistry.contains("docs2ai_file_uploader")) {
    console.error("[Docs2AI] Widget 'docs2ai_file_uploader' not found in registry after import!");
    console.error("[Docs2AI] This may indicate the widget file failed to load. Check for JavaScript errors.");
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

