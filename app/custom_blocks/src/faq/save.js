import { RichText } from '@wordpress/block-editor';
import { useBlockProps } from '@wordpress/block-editor';

export default function Save({ attributes }) {
    const blockProps = useBlockProps.save();
    const { question, answer } = attributes;

    return (
        <details { ...blockProps } className="wp-block-aeo-faq">
            <summary>
                <RichText.Content value={question} />
            </summary>
            <div className="aeo-faq-answer-content">
                <RichText.Content value={answer} />
            </div>
        </details>
    );
}
