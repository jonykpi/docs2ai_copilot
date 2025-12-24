/** @odoo-module **/

import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { onMounted, onWillUnmount, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

const DOCS2AI_STATUS_POLL_INTERVAL = 15000;

async function startDocs2aiStatusPolling(component) {
    stopDocs2aiStatusPolling(component);
    await refreshDocs2aiStatus(component, true);
    component.docs2aiPollingHandle = window.setInterval(() => {
        void refreshDocs2aiStatus(component);
    }, DOCS2AI_STATUS_POLL_INTERVAL);
}

function stopDocs2aiStatusPolling(component) {
    if (component.docs2aiPollingHandle) {
        window.clearInterval(component.docs2aiPollingHandle);
        component.docs2aiPollingHandle = null;
    }
}

async function refreshDocs2aiStatus(component, isInitial = false) {
    if (!component.isDocs2aiEnabled || component.docs2aiFetchInProgress) {
        return;
    }

    component.docs2aiFetchInProgress = true;
    component.docs2aiState.loading = true;
    updateVerifyButtonDom(component);
    try {
        const result = await component.orm.call("account.move", "docs2ai_get_verification_status", [], {});
        component.docs2aiState.pendingCount = result?.total_pending ?? 0;
        component.docs2aiState.isRunning = Boolean(result?.is_running);
        component.docs2aiState.errorNotified = false;
        updateVerifyButtonDom(component);
    } catch (error) {
        if (!component.docs2aiState.errorNotified && !isInitial) {
            component.notification?.add(
                _t("Unable to refresh Docs2AI verification status. Please check your configuration."),
                { type: "warning" }
            );
            component.docs2aiState.errorNotified = true;
        }
    } finally {
        component.docs2aiState.loading = false;
        component.docs2aiFetchInProgress = false;
        updateVerifyButtonDom(component);
    }
}

function findVerifyButton(component) {
    // Try multiple selectors and locations
    let button = null;
    
    // First try in component element
    if (component.el) {
        button = component.el.querySelector('button[name="action_open_scanner_link"]');
    }
    
    // Try in document
    if (!button) {
        button = document.querySelector('button[name="action_open_scanner_link"]');
    }
    
    // Try alternative selectors
    if (!button) {
        button = document.querySelector('button[data-name="action_open_scanner_link"]');
    }
    
    // Try by text content
    if (!button) {
        const allButtons = document.querySelectorAll('button');
        for (const btn of allButtons) {
            if (btn.textContent && btn.textContent.trim().toLowerCase().includes('verify')) {
                button = btn;
                break;
            }
        }
    }
    
    return button;
}

function updateVerifyButtonDom(component) {
    if (!component.isDocs2aiEnabled) {
        return;
    }
    
    const button = findVerifyButton(component);
    
    if (!button) {
        // Retry after a short delay
        setTimeout(() => {
            const retryButton = findVerifyButton(component);
            if (retryButton) {
                updateVerifyButtonDom(component);
            }
        }, 500);
        return;
    }

    initializeVerifyButton(button);

    const baseLabel = button.dataset.docs2aiBaseLabel || _t("Verify");
    const count = component.docs2aiState.pendingCount || 0;
    // Always show count if it's greater than 0
    const labelText = count > 0 ? `${baseLabel} (${count})` : baseLabel;
    
    const labelEl = button.querySelector(".docs2ai-verify-text");
    if (labelEl) {
        labelEl.textContent = labelText;
    }
    button.setAttribute("aria-label", labelText);

    // Show spinner when is_running is true
    const spinner = button.querySelector(".docs2ai-spinner");
    const shouldShowSpinner = component.docs2aiState.isRunning === true;
    if (spinner) {
        if (shouldShowSpinner) {
            spinner.classList.add("is-active");
        } else {
            spinner.classList.remove("is-active");
        }
    }
}

function initializeVerifyButton(button) {
    if (button.dataset.docs2aiEnhanced === "1") {
        return;
    }

    const originalIcon = button.querySelector("i");
    const iconClone = originalIcon ? originalIcon.cloneNode(true) : null;
    const baseLabel = (button.textContent || "").trim() || _t("Verify");

    // Clear button content
    button.textContent = "";
    button.classList.add("docs2ai-verify-button");
    button.dataset.docs2aiBaseLabel = baseLabel;

    // Add icon if it exists
    if (iconClone) {
        button.appendChild(iconClone);
    }

    // Add spinner element
    const spinner = document.createElement("span");
    spinner.className = "docs2ai-spinner";
    spinner.setAttribute("aria-hidden", "true");
    button.appendChild(spinner);

    // Add text label element
    const label = document.createElement("span");
    label.className = "docs2ai-verify-text";
    button.appendChild(label);

    button.dataset.docs2aiEnhanced = "1";
}

// Patch the ListController directly - it will check resModel in setup()
const originalSetup = ListController.prototype.setup;
ListController.prototype.setup = function(...args) {
    const result = originalSetup.apply(this, args);
    
    // Enable for account.move and hr.expense
    if (this.props?.resModel === "account.move" || this.props?.resModel === "hr.expense") {
        try {
            this.orm = this.orm || useService("orm");
            this.notification = this.notification || useService("notification");
            this.isDocs2aiEnabled = true;
            
            // useState must be called directly in setup
            this.docs2aiState = useState({
                pendingCount: 0,
                isRunning: false,
                loading: false,
                errorNotified: false,
            });
            this.docs2aiPollingHandle = null;
            this.docs2aiFetchInProgress = false;

            onMounted(() => {
                setTimeout(() => {
                    updateVerifyButtonDom(this);
                    void startDocs2aiStatusPolling(this);
                }, 100);
            });
            onWillUnmount(() => {
                stopDocs2aiStatusPolling(this);
            });
        } catch (error) {
            // Silently fail - don't break the list view if Docs2AI setup fails
        }
    }
    
    return result;
};
