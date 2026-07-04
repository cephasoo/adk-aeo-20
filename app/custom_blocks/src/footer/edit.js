import { InspectorControls, useBlockProps } from '@wordpress/block-editor';
import { PanelBody, TextControl, TextareaControl, Button } from '@wordpress/components';

export default function Edit({ attributes, setAttributes }) {
    const blockProps = useBlockProps({ className: 'wp-block-aeo-footer' });
    const {
        brandText,
        description,
        column1Title,
        column1Links,
        column2Title,
        column2Links,
        column3Title,
        column3Links,
        statusText,
        copyrightText
    } = attributes;

    const updateLink = (links, index, field, value, setLinks) => {
        const updated = [...links];
        updated[index] = { ...updated[index], [field]: value };
        setLinks(updated);
    };

    const addLink = (links, setLinks) => {
        setLinks([...links, { label: 'New Link', url: '#' }]);
    };

    const removeLink = (links, index, setLinks) => {
        const updated = links.filter((_, i) => i !== index);
        setLinks(updated);
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
                    <TextareaControl
                        label="Brand Description"
                        value={description}
                        onChange={(val) => setAttributes({ description: val })}
                    />
                </PanelBody>

                <PanelBody title="Column 1 Settings" initialOpen={false}>
                    <TextControl
                        label="Column 1 Title"
                        value={column1Title}
                        onChange={(val) => setAttributes({ column1Title: val })}
                    />
                    {column1Links.map((link, i) => (
                        <div key={i} className="edit-link-item">
                            <TextControl
                                label={`Link ${i + 1} Label`}
                                value={link.label}
                                onChange={(val) => updateLink(column1Links, i, 'label', val, (val) => setAttributes({ column1Links: val }))}
                            />
                            <TextControl
                                label={`Link ${i + 1} URL`}
                                value={link.url}
                                onChange={(val) => updateLink(column1Links, i, 'url', val, (val) => setAttributes({ column1Links: val }))}
                            />
                            <Button isDestructive isSmall onClick={() => removeLink(column1Links, i, (val) => setAttributes({ column1Links: val }))}>
                                Remove
                            </Button>
                        </div>
                    ))}
                    <Button isPrimary isSmall onClick={() => addLink(column1Links, (val) => setAttributes({ column1Links: val }))}>
                        + Add Link
                    </Button>
                </PanelBody>

                <PanelBody title="Column 2 Settings" initialOpen={false}>
                    <TextControl
                        label="Column 2 Title"
                        value={column2Title}
                        onChange={(val) => setAttributes({ column2Title: val })}
                    />
                    {column2Links.map((link, i) => (
                        <div key={i} className="edit-link-item">
                            <TextControl
                                label={`Link ${i + 1} Label`}
                                value={link.label}
                                onChange={(val) => updateLink(column2Links, i, 'label', val, (val) => setAttributes({ column2Links: val }))}
                            />
                            <TextControl
                                label={`Link ${i + 1} URL`}
                                value={link.url}
                                onChange={(val) => updateLink(column2Links, i, 'url', val, (val) => setAttributes({ column2Links: val }))}
                            />
                            <Button isDestructive isSmall onClick={() => removeLink(column2Links, i, (val) => setAttributes({ column2Links: val }))}>
                                Remove
                            </Button>
                        </div>
                    ))}
                    <Button isPrimary isSmall onClick={() => addLink(column2Links, (val) => setAttributes({ column2Links: val }))}>
                        + Add Link
                    </Button>
                </PanelBody>

                <PanelBody title="Column 3 Settings" initialOpen={false}>
                    <TextControl
                        label="Column 3 Title"
                        value={column3Title}
                        onChange={(val) => setAttributes({ column3Title: val })}
                    />
                    {column3Links.map((link, i) => (
                        <div key={i} className="edit-link-item">
                            <TextControl
                                label={`Link ${i + 1} Label`}
                                value={link.label}
                                onChange={(val) => updateLink(column3Links, i, 'label', val, (val) => setAttributes({ column3Links: val }))}
                            />
                            <TextControl
                                label={`Link ${i + 1} URL`}
                                value={link.url}
                                onChange={(val) => updateLink(column3Links, i, 'url', val, (val) => setAttributes({ column3Links: val }))}
                            />
                            <Button isDestructive isSmall onClick={() => removeLink(column3Links, i, (val) => setAttributes({ column3Links: val }))}>
                                Remove
                            </Button>
                        </div>
                    ))}
                    <Button isPrimary isSmall onClick={() => addLink(column3Links, (val) => setAttributes({ column3Links: val }))}>
                        + Add Link
                    </Button>
                </PanelBody>

                <PanelBody title="Footer Metadata" initialOpen={false}>
                    <TextControl
                        label="Status Text"
                        value={statusText}
                        onChange={(val) => setAttributes({ statusText: val })}
                    />
                    <TextControl
                        label="Copyright Text"
                        value={copyrightText}
                        onChange={(val) => setAttributes({ copyrightText: val })}
                    />
                </PanelBody>
            </InspectorControls>

            {/* Block Editor Preview */}
            <footer className="aeo-footer-preview">
                <div className="aeo-footer-grid">
                    <div className="footer-col brand-col">
                        <h3 className="brand-logo">{brandText}</h3>
                        <p className="brand-desc">{description}</p>
                    </div>
                    <div className="footer-col">
                        <h4>{column1Title}</h4>
                        <ul>{column1Links.map((l, i) => <li key={i}>{l.label}</li>)}</ul>
                    </div>
                    <div className="footer-col">
                        <h4>{column2Title}</h4>
                        <ul>{column2Links.map((l, i) => <li key={i}>{l.label}</li>)}</ul>
                    </div>
                    <div className="footer-col">
                        <h4>{column3Title}</h4>
                        <ul>{column3Links.map((l, i) => <li key={i}>{l.label}</li>)}</ul>
                    </div>
                </div>
                <div className="aeo-footer-bottom">
                    <p className="copyright">{copyrightText}</p>
                    <div className="status-badge">
                        <span className="pulse-indicator"></span>
                        <span className="status-txt">{statusText}</span>
                    </div>
                </div>
            </footer>
        </div>
    );
}
