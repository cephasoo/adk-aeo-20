import { InspectorControls, useBlockProps } from '@wordpress/block-editor';
import { PanelBody, TextControl, TextareaControl, SelectControl, ToggleControl, Button } from '@wordpress/components';

export default function Edit({ attributes, setAttributes }) {
    const blockProps = useBlockProps({ className: 'wp-block-aeo-form' });
    const { formTitle, formSubtitle, submitText, fields } = attributes;

    const updateField = (index, key, value) => {
        const updated = [...fields];
        updated[index] = { ...updated[index], [key]: value };
        setAttributes({ fields: updated });
    };

    const addField = () => {
        const newField = {
            id: `field_${Date.now()}`,
            type: 'text',
            label: 'New Field Label',
            placeholder: 'Enter text...',
            required: false
        };
        setAttributes({ fields: [...fields, newField] });
    };

    const removeField = (index) => {
        const updated = fields.filter((_, i) => i !== index);
        setAttributes({ fields: updated });
    };

    return (
        <div {...blockProps}>
            <InspectorControls>
                <PanelBody title="Form Headers" initialOpen={true}>
                    <TextControl
                        label="Form Title"
                        value={formTitle}
                        onChange={(val) => setAttributes({ formTitle: val })}
                    />
                    <TextareaControl
                        label="Form Subtitle"
                        value={formSubtitle}
                        onChange={(val) => setAttributes({ formSubtitle: val })}
                    />
                    <TextControl
                        label="Submit Button Text"
                        value={submitText}
                        onChange={(val) => setAttributes({ submitText: val })}
                    />
                </PanelBody>

                <PanelBody title="Form Fields Editor" initialOpen={true}>
                    {fields.map((field, i) => (
                        <div key={i} className="edit-field-block">
                            <SelectControl
                                label={`Field ${i + 1} Type`}
                                value={field.type}
                                options={[
                                    { label: 'Text Input', value: 'text' },
                                    { label: 'Email Input', value: 'email' },
                                    { label: 'Phone Number (Tel)', value: 'tel' },
                                    { label: 'Dropdown Select', value: 'select' },
                                    { label: 'Large Text (Textarea)', value: 'textarea' },
                                    { label: 'File Upload', value: 'file' }
                                ]}
                                onChange={(val) => updateField(i, 'type', val)}
                            />
                            <TextControl
                                label="Field Label"
                                value={field.label}
                                onChange={(val) => updateField(i, 'label', val)}
                            />
                            {field.type !== 'select' && (
                                <TextControl
                                    label="Placeholder Text"
                                    value={field.placeholder}
                                    onChange={(val) => updateField(i, 'placeholder', val)}
                                />
                            )}
                            {field.type === 'select' && (
                                <TextareaControl
                                    label="Dropdown Options (Comma Separated)"
                                    value={field.options || ''}
                                    onChange={(val) => updateField(i, 'options', val)}
                                    help="Example: Option 1, Option 2, Option 3"
                                />
                            )}
                            <ToggleControl
                                label="Is Field Required?"
                                checked={!!field.required}
                                onChange={(val) => updateField(i, 'required', val)}
                            />
                            <Button isDestructive isSmall onClick={() => removeField(i)}>
                                Remove Field
                            </Button>
                        </div>
                    ))}
                    <Button isPrimary isSmall onClick={addField} style={{ marginTop: '12px' }}>
                        + Add Form Field
                    </Button>
                </PanelBody>
            </InspectorControls>

            {/* Block Editor Preview */}
            <div className="aeo-form-wrapper">
                <header className="aeo-form-header">
                    <h3>{formTitle}</h3>
                    <p>{formSubtitle}</p>
                </header>
                <form className="aeo-form" onSubmit={(e) => e.preventDefault()}>
                    {fields.map((field, i) => {
                        const fieldId = `field_${i}`;
                        return (
                            <div key={i} className="form-group">
                                <label htmlFor={fieldId}>
                                    {field.label} {field.required && <span className="required-star">*</span>}
                                </label>
                                {field.type === 'textarea' ? (
                                    <textarea id={fieldId} placeholder={field.placeholder} disabled></textarea>
                                ) : field.type === 'select' ? (
                                    <select id={fieldId} disabled>
                                        <option value="">Choose an option...</option>
                                        {(field.options || '').split(',').map((opt, idx) => (
                                            <option key={idx} value={opt.trim()}>{opt.trim()}</option>
                                        ))}
                                    </select>
                                ) : field.type === 'file' ? (
                                    <input type="file" id={fieldId} disabled />
                                ) : (
                                    <input type={field.type} id={fieldId} placeholder={field.placeholder} disabled />
                                )}
                            </div>
                        );
                    })}
                    <div className="form-submit-wrap">
                        <button type="button" className="aeo-form-submit-btn">{submitText}</button>
                    </div>
                </form>
            </div>
        </div>
    );
}
