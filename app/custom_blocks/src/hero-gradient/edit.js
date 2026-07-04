import { RichText, InspectorControls } from '@wordpress/block-editor';
import { PanelBody, TextControl } from '@wordpress/components';
import { useBlockProps } from '@wordpress/block-editor';
import { useSelect } from '@wordpress/data';

export default function Edit({ attributes, setAttributes }) {
    const blockProps = useBlockProps({ className: 'wp-block-aeo-hero-gradient' });
    const { title, subtitle, ctaText, ctaUrl } = attributes;

    const postTitle = useSelect((select) => {
        return select('core/editor').getEditedPostAttribute('title');
    }, []);

    const displayTitle = title || postTitle || 'Hero Title';

    return (
        <div { ...blockProps }>
            <InspectorControls>
                <PanelBody title="CTA Settings" initialOpen={true}>
                    <TextControl
                        label="CTA Link URL"
                        value={ctaUrl}
                        onChange={(val) => setAttributes({ ctaUrl: val })}
                    />
                </PanelBody>
            </InspectorControls>

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
