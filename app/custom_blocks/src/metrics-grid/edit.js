import { InspectorControls, useBlockProps } from '@wordpress/block-editor';
import { PanelBody, RangeControl, Button, TextControl, ColorPalette } from '@wordpress/components';

export default function Edit({ attributes, setAttributes }) {
    const { columns, metrics, outerBgColor, innerBgColor } = attributes;

    const blockProps = useBlockProps({
        className: 'wp-block-aeo-metrics-grid',
        style: outerBgColor ? { backgroundColor: outerBgColor } : {}
    });

    const updateMetric = (index, key, val) => {
        const newMetrics = [...metrics];
        newMetrics[index] = { ...newMetrics[index], [key]: val };
        setAttributes({ metrics: newMetrics });
    };

    const addCard = () => {
        const newMetrics = [...metrics, { value: 'New Stat', label: 'Description', badgeText: 'New' }];
        setAttributes({ metrics: newMetrics });
    };

    const removeCard = (index) => {
        const newMetrics = metrics.filter((_, i) => i !== index);
        setAttributes({ metrics: newMetrics });
    };

    return (
        <div {...blockProps}>
            <InspectorControls>
                <PanelBody title="Grid Settings" initialOpen={true}>
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

            <div className="aeo-metrics-builder-wrapper">
                <h4>Case Study Metrics Grid Editor</h4>
                <p className="builder-help-text">Edit the numbers, labels, and badges directly below. Click '+' to add a card.</p>

                <div className={`aeo-metrics-grid cols-${columns}`}>
                    {metrics.map((metric, index) => (
                        <div key={index} className="aeo-metric-card-edit" style={innerBgColor ? { backgroundColor: innerBgColor } : {}}>
                            <span className="remove-card-btn" onClick={() => removeCard(index)} title="Remove Card">&times;</span>

                            <TextControl
                                className="edit-metric-badge"
                                value={metric.badgeText}
                                onChange={(val) => updateMetric(index, 'badgeText', val)}
                                placeholder="Badge (e.g. Verified)"
                            />
                            <TextControl
                                className="edit-metric-value"
                                value={metric.value}
                                onChange={(val) => updateMetric(index, 'value', val)}
                                placeholder="Value (e.g. +340%)"
                            />
                            <TextControl
                                className="edit-metric-label"
                                value={metric.label}
                                onChange={(val) => updateMetric(index, 'label', val)}
                                placeholder="Label text"
                            />
                        </div>
                    ))}

                    <div className="add-metric-card-trigger" onClick={addCard} style={innerBgColor ? { backgroundColor: innerBgColor } : {}}>
                        <span>+ Add Metric Card</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
