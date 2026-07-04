import { registerBlockType } from '@wordpress/blocks';
import edit from './edit';
import metadata from './block.json';
import './style.scss';
import './editor.scss';

registerBlockType(metadata.name, {
    edit,
    save: () => null,
});

// Register legacy name to resolve Gutenberg un-supported block error in editor
registerBlockType('aeo-custom-blocks/hero', {
    title: 'AEO Hero (Legacy)',
    category: 'design',
    icon: 'cover-image',
    attributes: metadata.attributes,
    supports: metadata.supports,
    edit,
    save: () => null,
});
