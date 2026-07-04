import { InspectorControls, RichText, useBlockProps } from '@wordpress/block-editor';
import { PanelBody, SelectControl, ToggleControl } from '@wordpress/components';

export default function Edit({ attributes, setAttributes }) {
    const blockProps = useBlockProps({ className: 'wp-block-aeo-alert' });
    const { type, message, dismissible } = attributes;

    const alertIcons = {
        success: (
            <svg className="alert-icon" viewBox="0 0 24 24" fill="none" stroke="#34d399" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
        ),
        info: (
            <svg className="alert-icon" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
        ),
        warning: (
            <svg className="alert-icon" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
        ),
        error: (
            <svg className="alert-icon" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
        )
    };

    return (
        <div {...blockProps}>
            <InspectorControls>
                <PanelBody title="Alert Settings" initialOpen={true}>
                    <SelectControl
                        label="Alert Type"
                        value={type}
                        options={[
                            { label: 'Success (Green)', value: 'success' },
                            { label: 'Info (Blue)', value: 'info' },
                            { label: 'Warning (Amber)', value: 'warning' },
                            { label: 'Error (Red)', value: 'error' }
                        ]}
                        onChange={(val) => setAttributes({ type: val })}
                    />
                    <ToggleControl
                        label="Dismissible Alert?"
                        checked={dismissible}
                        onChange={(val) => setAttributes({ dismissible: val })}
                    />
                </PanelBody>
            </InspectorControls>

            {/* Block Editor Preview */}
            <div className={`aeo-alert-banner ${type}`}>
                <div className="alert-body">
                    {alertIcons[type]}
                    <RichText
                        tagName="div"
                        className="alert-content"
                        value={message}
                        onChange={(val) => setAttributes({ message: val })}
                        placeholder="Enter alert message..."
                    />
                </div>
                {dismissible && (
                    <button type="button" className="alert-close" disabled>&times;</button>
                )}
            </div>
        </div>
    );
}
