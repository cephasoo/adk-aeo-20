import { InspectorControls, useBlockProps } from '@wordpress/block-editor';
import { PanelBody, ColorPalette, Button, TextControl, TextareaControl, RangeControl } from '@wordpress/components';

export default function Edit({ attributes, setAttributes }) {
    const { activeColor, steps, outerBgColor, innerBgColor, columns } = attributes;

    const blockProps = useBlockProps({
        className: 'wp-block-aeo-workflow',
        style: {
            '--active-color': activeColor,
            ...(outerBgColor ? { backgroundColor: outerBgColor } : {})
        }
    });

    const updateStep = (index, key, val) => {
        const newSteps = [...steps];
        newSteps[index] = { ...newSteps[index], [key]: val };
        setAttributes({ steps: newSteps });
    };

    const addStep = () => {
        const newSteps = [...steps, { number: String(steps.length + 1).padStart(2, '0'), title: 'New Step', description: 'Describe this step.' }];
        setAttributes({ steps: newSteps });
    };

    const removeStep = (index) => {
        const newSteps = steps.filter((_, i) => i !== index);
        // Automatically re-sequence numbers
        const resequenced = newSteps.map((step, i) => ({
            ...step,
            number: String(i + 1).padStart(2, '0')
        }));
        setAttributes({ steps: resequenced });
    };

    return (
        <div {...blockProps}>
            <InspectorControls>
                <PanelBody title="Workflow Visuals" initialOpen={true}>
                    <label className="color-palette-label">Active Glow Color</label>
                    <ColorPalette
                        value={activeColor}
                        onChange={(val) => setAttributes({ activeColor: val })}
                    />
                </PanelBody>

                <PanelBody title="Layout Settings" initialOpen={true}>
                    <RangeControl
                        label="Grid Columns"
                        value={columns}
                        onChange={(val) => setAttributes({ columns: val })}
                        min={1}
                        max={4}
                    />
                </PanelBody>

                <PanelBody title="Color Settings" initialOpen={false}>
                    <label className="color-palette-label">Outer Section Background</label>
                    <ColorPalette
                        value={outerBgColor}
                        onChange={(val) => setAttributes({ outerBgColor: val })}
                    />
                    <label className="color-palette-label" style={{ marginTop: '15px', display: 'block' }}>Inner Card Background</label>
                    <ColorPalette
                        value={innerBgColor}
                        onChange={(val) => setAttributes({ innerBgColor: val })}
                    />
                </PanelBody>
            </InspectorControls>

            <div className="aeo-workflow-builder-wrapper">
                <h4>Agentic Workflow Timeline Editor</h4>
                <p className="builder-help-text">Build the automation sequence. Click '+' to add a step.</p>

                <div className="aeo-workflow-editor-grid">
                    {steps.map((step, index) => (
                        <div key={index} className="aeo-workflow-step-edit-card" style={innerBgColor ? { backgroundColor: innerBgColor } : {}}>
                            <span className="remove-step-btn" onClick={() => removeStep(index)} title="Remove Step">&times;</span>

                            <div className="edit-step-header">
                                <TextControl
                                    className="edit-step-number"
                                    value={step.number}
                                    onChange={(val) => updateStep(index, 'number', val)}
                                    placeholder="01"
                                />
                                <TextControl
                                    className="edit-step-title"
                                    value={step.title}
                                    onChange={(val) => updateStep(index, 'title', val)}
                                    placeholder="Step Title"
                                />
                            </div>
                            <TextareaControl
                                className="edit-step-desc"
                                value={step.description}
                                onChange={(val) => updateStep(index, 'description', val)}
                                placeholder="Explain what happens in this stage..."
                            />
                        </div>
                    ))}

                    <div className="add-workflow-step-trigger" onClick={addStep} style={innerBgColor ? { backgroundColor: innerBgColor } : {}}>
                        <span>+ Add Step</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
