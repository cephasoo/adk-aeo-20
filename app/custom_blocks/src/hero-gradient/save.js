import { RichText } from '@wordpress/block-editor';
import { useBlockProps } from '@wordpress/block-editor';

export default function Save({ attributes }) {
    const blockProps = useBlockProps.save();
    const { title, subtitle, ctaText, ctaUrl } = attributes;

    return (
        <div { ...blockProps } className="wp-block-aeo-hero">
            <header className="aeo-hero-header">
                <RichText.Content tagName="h1" value={title} />
                <RichText.Content tagName="p" className="aeo-hero-subtitle" value={subtitle} />
                {ctaText && (
                    <div className="aeo-hero-cta">
                        <a href={ctaUrl} className="aeo-hero-cta-btn">
                            {ctaText}
                        </a>
                    </div>
                )}
            </header>
        </div>
    );
}
