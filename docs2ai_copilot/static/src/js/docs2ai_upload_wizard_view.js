/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { Docs2AIUploadWizardController } from "./drag_drop_files";
import { docs2aiFileUploader } from "./docs2ai_file_uploader";

// Register the widget here to ensure it's available when the view loads
registry.category("view_widgets").add("docs2ai_file_uploader", docs2aiFileUploader);

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

