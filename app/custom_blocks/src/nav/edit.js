import { InspectorControls, useBlockProps } from '@wordpress/block-editor';
import { PanelBody, TextControl, Button } from '@wordpress/components';

export default function Edit({ attributes, setAttributes }) {
    const blockProps = useBlockProps({ className: 'wp-block-aeo-nav' });
    const { brandText, links, ctaText, ctaUrl } = attributes;

    const updateLink = (index, field, value) => {
        const updated = [...links];
        updated[index] = { ...updated[index], [field]: value };
        setAttributes({ links: updated });
    };

    const addLink = () => {
        setAttributes({ links: [...links, { label: 'New Link', url: '#' }] });
    };

    const removeLink = (index) => {
        const updated = links.filter((_, i) => i !== index);
        setAttributes({ links: updated });
    };

    return (
        <div {...blockProps}>
            <InspectorControls>
                <PanelBody title="Brand Settings" initialOpen={true}>
                    <TextControl
                        label="Brand Text"
                        value={brandText}
                        onChange={(val) => setAttributes({ brandText: val })}
                    />
                </PanelBody>
                <PanelBody title="Navigation Links" initialOpen={true}>
                    {links.map((link, i) => (
                        <div key={i} style={{ marginBottom: '12px', padding: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>
                            <TextControl
                                label={`Link ${i + 1} Label`}
                                value={link.label}
                                onChange={(val) => updateLink(i, 'label', val)}
                            />
                            <TextControl
                                label={`Link ${i + 1} URL`}
                                value={link.url}
                                onChange={(val) => updateLink(i, 'url', val)}
                            />
                            <Button
                                isDestructive
                                isSmall
                                onClick={() => removeLink(i)}
                            >
                                Remove
                            </Button>
                        </div>
                    ))}
                    <Button isPrimary isSmall onClick={addLink}>
                        + Add Link
                    </Button>
                </PanelBody>
                <PanelBody title="CTA Button" initialOpen={true}>
                    <TextControl
                        label="CTA Text"
                        value={ctaText}
                        onChange={(val) => setAttributes({ ctaText: val })}
                    />
                    <TextControl
                        label="CTA URL"
                        value={ctaUrl}
                        onChange={(val) => setAttributes({ ctaUrl: val })}
                    />
                </PanelBody>
            </InspectorControls>

            {/* Editor preview of the nav bar */}
            <nav className="aeo-nav-bar">
                <div className="aeo-nav-brand">{brandText}</div>
                <ul className="aeo-nav-links">
                    {links.map((link, i) => (
                        <li key={i} className="aeo-nav-link-item">
                            <span>{link.label}</span>
                        </li>
                    ))}
                </ul>
                <div className="aeo-nav-cta-wrap">
                    <span className="aeo-nav-cta-btn">{ctaText}</span>
                </div>
                <div className="aeo-nav-burger">
                    <span></span><span></span><span></span>
                </div>
            </nav>
        </div>
    );
}
