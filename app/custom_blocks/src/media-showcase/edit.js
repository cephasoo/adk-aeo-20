import { InspectorControls, useBlockProps, MediaUpload } from '@wordpress/block-editor';
import { PanelBody, TextControl, TextareaControl, Button, ColorPalette, SelectControl } from '@wordpress/components';

export default function Edit({ attributes, setAttributes }) {
    const { title, subtitle, ctaText, ctaUrl, outerBgColor, innerBgColor, testimonials, imageLoading } = attributes;

    const blockProps = useBlockProps({
        className: 'wp-block-aeo-media-showcase',
        style: outerBgColor ? { backgroundColor: outerBgColor } : {}
    });

    const updateTestimonial = (index, key, val) => {
        const updated = [...testimonials];
        updated[index] = { ...updated[index], [key]: val };
        setAttributes({ testimonials: updated });
    };

    const addTestimonial = () => {
        setAttributes({
            testimonials: [
                ...testimonials,
                { quote: 'New testimonial quote...', expandedQuote: '', author: 'Name', role: 'Role', imageUrl: '', imageAlt: 'Portrait' }
            ]
        });
    };

    const removeTestimonial = (index) => {
        const updated = testimonials.filter((_, i) => i !== index);
        setAttributes({ testimonials: updated });
    };

    return (
        <div {...blockProps}>
            <InspectorControls>
                <PanelBody title="Header Settings" initialOpen={true}>
                    <TextControl
                        label="Main Title"
                        value={title}
                        onChange={(val) => setAttributes({ title: val })}
                    />
                    <TextareaControl
                        label="Subheading"
                        value={subtitle}
                        onChange={(val) => setAttributes({ subtitle: val })}
                    />
                </PanelBody>

                <PanelBody title="Call To Action Settings" initialOpen={true}>
                    <TextControl
                        label="CTA Button Text"
                        value={ctaText}
                        onChange={(val) => setAttributes({ ctaText: val })}
                    />
                    <TextControl
                        label="CTA Link URL"
                        value={ctaUrl}
                        onChange={(val) => setAttributes({ ctaUrl: val })}
                    />
                </PanelBody>

                <PanelBody title="SEO & Performance Settings" initialOpen={true}>
                    <SelectControl
                        label="Image Loading Mode"
                        value={imageLoading}
                        options={[
                            { label: 'Lazy (Below Fold - SEO Optimized)', value: 'lazy' },
                            { label: 'Eager (Above Fold - LCP Optimized)', value: 'eager' }
                        ]}
                        onChange={(val) => setAttributes({ imageLoading: val })}
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

            <div className="aeo-showcase-builder-wrapper">
                <h4>AEO Testimonials & Media Showcase Editor</h4>
                <p className="builder-help-text">Build the testimonials grid below. Click '+' to add a testimonial card.</p>

                <div className="aeo-showcase-editor-header-preview">
                    <h2>{title || 'Header Text'}</h2>
                    <p>{subtitle || 'Subheading text...'}</p>
                </div>

                <div className="aeo-showcase-editor-grid">
                    {testimonials.map((item, index) => (
                        <div key={index} className="aeo-showcase-edit-card" style={innerBgColor ? { backgroundColor: innerBgColor } : {}}>
                            <span className="remove-card-btn" onClick={() => removeTestimonial(index)} title="Remove Testimonial">&times;</span>

                            <div className="edit-card-image-wrap">
                                {item.imageUrl ? (
                                    <div className="avatar-preview-container">
                                        <img src={item.imageUrl} alt={item.imageAlt} className="avatar-preview-img" />
                                        <Button isLink isDestructive onClick={() => updateTestimonial(index, 'imageUrl', '')}>
                                            Remove Image
                                        </Button>
                                    </div>
                                ) : (
                                    <MediaUpload
                                        onSelect={(media) => updateTestimonial(index, 'imageUrl', media.url)}
                                        allowedTypes={['image']}
                                        value={item.imageUrl}
                                        render={({ open }) => (
                                            <Button isSecondary onClick={open}>
                                                Upload Avatar/Logo
                                            </Button>
                                        )}
                                    />
                                )}
                            </div>

                            <TextControl
                                label="Image ALT Text (SEO)"
                                value={item.imageAlt}
                                onChange={(val) => updateTestimonial(index, 'imageAlt', val)}
                                placeholder="Describe the image..."
                            />

                            <TextareaControl
                                label="Quote Summary"
                                value={item.quote}
                                onChange={(val) => updateTestimonial(index, 'quote', val)}
                                placeholder="Short testimonial quote..."
                            />

                            <TextareaControl
                                label="Expandable Detailed Story (Optional)"
                                value={item.expandedQuote}
                                onChange={(val) => updateTestimonial(index, 'expandedQuote', val)}
                                placeholder="Longer detailed case study story..."
                            />

                            <div className="edit-card-author-row">
                                <TextControl
                                    label="Author Name"
                                    value={item.author}
                                    onChange={(val) => updateTestimonial(index, 'author', val)}
                                />
                                <TextControl
                                    label="Author Role/Company"
                                    value={item.role}
                                    onChange={(val) => updateTestimonial(index, 'role', val)}
                                />
                            </div>

                            <div className="edit-card-author-row">
                                <TextControl
                                    label="Author Profile URL (e.g. LinkedIn)"
                                    value={item.authorUrl || ''}
                                    onChange={(val) => updateTestimonial(index, 'authorUrl', val)}
                                    placeholder="https://linkedin.com/..."
                                />
                                <TextControl
                                    label="Client Website / Case Study URL"
                                    value={item.companyUrl || ''}
                                    onChange={(val) => updateTestimonial(index, 'companyUrl', val)}
                                    placeholder="https://example.com/..."
                                />
                            </div>
                        </div>
                    ))}

                    <div className="add-card-trigger" onClick={addTestimonial} style={innerBgColor ? { backgroundColor: innerBgColor } : {}}>
                        <span>+ Add Testimonial Card</span>
                    </div>
                </div>

                {ctaText && (
                    <div className="aeo-showcase-cta-preview-wrap">
                        <span className="aeo-showcase-cta-btn">{ctaText}</span>
                    </div>
                )}
            </div>
        </div>
    );
}
