import { InspectorControls, useBlockProps } from '@wordpress/block-editor';
import { PanelBody, TextControl, RangeControl } from '@wordpress/components';

export default function Edit({ attributes, setAttributes }) {
    const blockProps = useBlockProps({ className: 'wp-block-aeo-calculator' });
    const { title, subtitle, hourlyRate, manualHours, multiplier, maintenanceCost, ctaText, ctaUrl } = attributes;

    // Run preview math
    const weeklySavings = Math.round(manualHours * hourlyRate * multiplier);
    const annualSavings = Math.round((weeklySavings * 52) - maintenanceCost);
    const annualHoursSaved = Math.round(manualHours * 52 * multiplier);

    return (
        <div {...blockProps}>
            <InspectorControls>
                <PanelBody title="Header Settings" initialOpen={true}>
                    <TextControl
                        label="Calculator Title"
                        value={title}
                        onChange={(val) => setAttributes({ title: val })}
                    />
                    <TextControl
                        label="Calculator Subtitle"
                        value={subtitle}
                        onChange={(val) => setAttributes({ subtitle: val })}
                    />
                </PanelBody>

                <PanelBody title="Default Constants" initialOpen={true}>
                    <RangeControl
                        label="Hourly Cost of Labor ($)"
                        value={hourlyRate}
                        onChange={(val) => setAttributes({ hourlyRate: val })}
                        min={10}
                        max={300}
                    />
                    <RangeControl
                        label="Weekly Manual Hours"
                        value={manualHours}
                        onChange={(val) => setAttributes({ manualHours: val })}
                        min={1}
                        max={168}
                    />
                    <RangeControl
                        label="Efficiency Multiplier (Savings %)"
                        value={Math.round(multiplier * 100)}
                        onChange={(val) => setAttributes({ multiplier: val / 100 })}
                        min={10}
                        max={100}
                        help="Percentage of manual time automated away."
                    />
                    <RangeControl
                        label="Annual Maintenance Cost ($)"
                        value={maintenanceCost}
                        onChange={(val) => setAttributes({ maintenanceCost: val })}
                        min={0}
                        max={20000}
                    />
                </PanelBody>

                <PanelBody title="Call To Action Settings" initialOpen={false}>
                    <TextControl
                        label="CTA Button Text"
                        value={ctaText}
                        onChange={(val) => setAttributes({ ctaText: val })}
                    />
                    <TextControl
                        label="CTA Button URL"
                        value={ctaUrl}
                        onChange={(val) => setAttributes({ ctaUrl: val })}
                    />
                </PanelBody>
            </InspectorControls>

            {/* Block Preview */}
            <div className="aeo-calc-container">
                <header className="aeo-calc-header">
                    <h4>{title}</h4>
                    <p>{subtitle}</p>
                </header>

                <div className="aeo-calc-grid">
                    {/* Controls Column */}
                    <div className="calc-sliders-wrap">
                        <div className="calc-slider-group">
                            <label>Weekly Manual Hours: <span>{manualHours} hrs</span></label>
                            <input type="range" min="1" max="168" value={manualHours} disabled />
                        </div>
                        <div className="calc-slider-group">
                            <label>Average Hourly Rate: <span>${hourlyRate}/hr</span></label>
                            <input type="range" min="10" max="300" value={hourlyRate} disabled />
                        </div>
                        <div className="calc-slider-group">
                            <label>Efficiency Multiplier: <span>{Math.round(multiplier * 100)}%</span></label>
                            <input type="range" min="10" max="100" value={Math.round(multiplier * 100)} disabled />
                        </div>
                    </div>

                    {/* Results Column */}
                    <div className="calc-results-wrap">
                        <div className="result-metric highlight">
                            <span className="metric-label">Estimated Net Annual Savings</span>
                            <span className="metric-value">${annualSavings.toLocaleString()}</span>
                        </div>
                        <div className="result-secondary">
                            <div className="result-metric">
                                <span className="metric-label">Weekly Savings</span>
                                <span className="metric-value">${weeklySavings.toLocaleString()}</span>
                            </div>
                            <div className="result-metric">
                                <span className="metric-label">Hours Reclaimed / Yr</span>
                                <span className="metric-value">{annualHoursSaved.toLocaleString()} hrs</span>
                            </div>
                        </div>
                        <div className="calc-cta-wrap">
                            <button type="button" className="calc-cta-btn">{ctaText}</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
