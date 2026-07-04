import { RichText } from '@wordpress/block-editor';
import { useBlockProps } from '@wordpress/block-editor';

export default function Edit({ attributes, setAttributes }) {
    const blockProps = useBlockProps({ className: 'wp-block-aeo-faq' });
    const { question, answer } = attributes;

    return (
        <div { ...blockProps }>
            <div className="aeo-faq-editor-label">AEO Semantic Accordion (Details/Summary)</div>
            <RichText
                tagName="div"
                className="aeo-faq-editor-question"
                value={question}
                onChange={(val) => setAttributes({ question: val })}
                placeholder="Enter FAQ Question..."
            />
            <RichText
                tagName="div"
                className="aeo-faq-editor-answer"
                value={answer}
                onChange={(val) => setAttributes({ answer: val })}
                placeholder="Enter FAQ Answer description..."
            />
        </div>
    );
}
