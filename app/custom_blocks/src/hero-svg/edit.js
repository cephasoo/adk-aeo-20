import { RichText, InspectorControls, MediaUpload, MediaUploadCheck } from '@wordpress/block-editor';
import { PanelBody, TextControl, Button } from '@wordpress/components';
import { useBlockProps } from '@wordpress/block-editor';
import { useSelect } from '@wordpress/data';

export default function Edit({ attributes, setAttributes }) {
    const blockProps = useBlockProps({ className: 'wp-block-aeo-hero-svg' });
    const { title, subtitle, ctaText, ctaUrl, svgUrl } = attributes;

    const postTitle = useSelect((select) => {
        return select('core/editor').getEditedPostAttribute('title');
    }, []);

    const displayTitle = title || postTitle || 'Hero Title';

    return (
        <div { ...blockProps }>
            <InspectorControls>
                <PanelBody title="Background Settings" initialOpen={true}>
                    <MediaUploadCheck>
                        <MediaUpload
                            onSelect={(media) => setAttributes({ svgUrl: media.url })}
                            allowedTypes={['image/svg+xml', 'image']}
                            value={svgUrl}
                            render={({ open }) => (
                                <div>
                                    {svgUrl ? (
                                        <div>
                                            <img src={svgUrl} alt="Custom Background Preview" style={{ maxWidth: '100%', marginBottom: '10px', maxHeight: '100px', display: 'block' }} />
                                            <div style={{ display: 'flex', gap: '8px' }}>
                                                <Button variant="secondary" onClick={open}>Replace SVG</Button>
                                                <Button variant="link" isDestructive onClick={() => setAttributes({ svgUrl: '' })}>Remove SVG</Button>
                                            </div>
                                        </div>
                                    ) : (
                                        <Button variant="primary" onClick={open}>Select SVG Background</Button>
                                    )}
                                </div>
                            )}
                        />
                    </MediaUploadCheck>
                </PanelBody>

                <PanelBody title="CTA Settings" initialOpen={false}>
                    <TextControl
                        label="CTA Link URL"
                        value={ctaUrl}
                        onChange={(val) => setAttributes({ ctaUrl: val })}
                    />
                </PanelBody>
            </InspectorControls>

            <div className="aeo-hero-svg-bg-preview">
                {svgUrl ? (
                    <div className="aeo-hero-custom-svg-edit" style={{ backgroundImage: `url(${svgUrl})`, backgroundSize: 'cover', backgroundPosition: 'center', position: 'absolute', width: '100%', height: '100%', top: 0, left: 0, zIndex: 1 }} />
                ) : (
                    <svg className="aeo-hero-svg-pattern-edit" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" width="100%" height="100%" preserveAspectRatio="xMidYMid slice">
                        <g fill="none" stroke="rgba(251, 191, 36, 0.15)" strokeWidth="2">
                            <path className="banana-vector-1" d="M100,80 C130,110 140,150 110,180 C95,150 80,110 100,80 Z" style={{ transformOrigin: '115px 130px' }} />
                            <path className="banana-vector-2" d="M600,250 C630,220 650,180 630,150 C610,180 580,220 600,250 Z" style={{ transformOrigin: '615px 200px' }} />
                            <path className="banana-vector-1" d="M200,300 C220,320 230,340 210,360 C200,340 190,320 200,300 Z" style={{ transformOrigin: '205px 330px' }} />
                            <path className="banana-vector-2" d="M700,70 C720,50 730,30 710,10 C700,30 690,50 700,70 Z" style={{ transformOrigin: '705px 40px' }} />
                        </g>
                    </svg>
                )}
            </div>

            <header className="aeo-hero-gradient-header">
                <RichText
                    tagName="h1"
                    value={displayTitle}
                    onChange={(val) => setAttributes({ title: val })}
                    placeholder="Enter Hero Title..."
                />
                <RichText
                    tagName="p"
                    className="aeo-hero-gradient-subtitle"
                    value={subtitle}
                    onChange={(val) => setAttributes({ subtitle: val })}
                    placeholder="Enter Subtitle description..."
                />
                <div className="aeo-hero-gradient-cta-btn">
                    <RichText
                        tagName="span"
                        className="btn-text"
                        value={ctaText}
                        onChange={(val) => setAttributes({ ctaText: val })}
                        placeholder="CTA Text..."
                    />
                </div>
            </header>
        </div>
    );
}
