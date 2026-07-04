<?php
/**
 * Plugin Name: AEO Custom Blocks
 * Description: Custom high-converting Gutenberg React blocks optimized for AEO (Answer Engine Optimization).
 * Version: 1.0.0
 * Author: Antigravity AEO Copilot
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

function aeo_register_custom_gutenberg_blocks() {
    // Register the Hero Gradient block
    if ( file_exists( __DIR__ . '/build/hero-gradient/block.json' ) ) {
        register_block_type( __DIR__ . '/build/hero-gradient', array(
            'render_callback' => 'aeo_render_hero_gradient_block',
        ) );
    }

    // Register the legacy Hero block for backward compatibility
    register_block_type( 'aeo-custom-blocks/hero', array(
        'render_callback' => 'aeo_render_hero_gradient_block',
        'style'           => 'aeo-custom-blocks-hero-gradient-style',
        'view_script'     => 'aeo-custom-blocks-hero-gradient-view-script',
    ) );

    // Register the Hero SVG block
    if ( file_exists( __DIR__ . '/build/hero-svg/block.json' ) ) {
        register_block_type( __DIR__ . '/build/hero-svg', array(
            'render_callback' => 'aeo_render_hero_svg_block',
        ) );
    }

    // Register the FAQ accordion block
    if ( file_exists( __DIR__ . '/build/faq/block.json' ) ) {
        register_block_type( __DIR__ . '/build/faq' );
    }

    // Register the Navigation Menu block
    if ( file_exists( __DIR__ . '/build/nav/block.json' ) ) {
        register_block_type( __DIR__ . '/build/nav', array(
            'render_callback' => 'aeo_render_nav_block',
        ) );
    }

    // Register the Footer block
    if ( file_exists( __DIR__ . '/build/footer/block.json' ) ) {
        register_block_type( __DIR__ . '/build/footer', array(
            'render_callback' => 'aeo_render_footer_block',
        ) );
    }

    // Register the Testimonials & Media Showcase block
    if ( file_exists( __DIR__ . '/build/media-showcase/block.json' ) ) {
        register_block_type( __DIR__ . '/build/media-showcase', array(
            'render_callback' => 'aeo_render_media_showcase_block',
        ) );
    }

    // Register the Form block
    if ( file_exists( __DIR__ . '/build/form/block.json' ) ) {
        register_block_type( __DIR__ . '/build/form', array(
            'render_callback' => 'aeo_render_form_block',
        ) );
    }

    // Register the Alert block
    if ( file_exists( __DIR__ . '/build/alert/block.json' ) ) {
        register_block_type( __DIR__ . '/build/alert', array(
            'render_callback' => 'aeo_render_alert_block',
        ) );
    }

    // Register the Calculator block
    if ( file_exists( __DIR__ . '/build/calculator/block.json' ) ) {
        register_block_type( __DIR__ . '/build/calculator', array(
            'render_callback' => 'aeo_render_calculator_block',
        ) );
    }

    // Register the Metrics Grid block
    if ( file_exists( __DIR__ . '/build/metrics-grid/block.json' ) ) {
        register_block_type( __DIR__ . '/build/metrics-grid', array(
            'render_callback' => 'aeo_render_metrics_grid_block',
        ) );
    }

    // Register the Workflow block
    if ( file_exists( __DIR__ . '/build/workflow/block.json' ) ) {
        register_block_type( __DIR__ . '/build/workflow', array(
            'render_callback' => 'aeo_render_workflow_block',
        ) );
    }

    // Register custom meta fields for AEO schema to expose them to REST API
    $meta_fields = array( 'aeo_schema_json', 'aeo_schema_type' );
    foreach ( array( 'post', 'page' ) as $post_type ) {
        foreach ( $meta_fields as $meta_key ) {
            register_post_meta(
                $post_type,
                $meta_key,
                array(
                    'show_in_rest' => true,
                    'single'       => true,
                    'type'         => 'string',
                    'auth_callback' => function() {
                        return current_user_can( 'edit_posts' );
                    }
                )
            );
        }
    }
}
add_action( 'init', 'aeo_register_custom_gutenberg_blocks' );

function aeo_render_hero_gradient_block( $attributes ) {
    $title = isset( $attributes['title'] ) && !empty( $attributes['title'] ) ? $attributes['title'] : get_the_title();
    $subtitle = isset( $attributes['subtitle'] ) ? $attributes['subtitle'] : '';
    $ctaText = isset( $attributes['ctaText'] ) ? $attributes['ctaText'] : '';
    $ctaUrl = isset( $attributes['ctaUrl'] ) ? $attributes['ctaUrl'] : '#';
    $align = isset( $attributes['align'] ) ? $attributes['align'] : '';

    $align_class = $align ? ' align' . $align : '';

    ob_start();
    ?>
    <div class="wp-block-aeo-hero-gradient<?php echo esc_attr( $align_class ); ?>">
        <header class="aeo-hero-gradient-header">
            <h1><?php echo esc_html( $title ); ?></h1>
            <?php if ( $subtitle ) : ?>
                <p class="aeo-hero-gradient-subtitle"><?php echo esc_html( $subtitle ); ?></p>
            <?php endif; ?>
            <?php if ( $ctaText ) : ?>
                <div class="aeo-hero-gradient-cta">
                    <a href="<?php echo esc_url( $ctaUrl ); ?>" class="aeo-hero-gradient-cta-btn"><?php echo esc_html( $ctaText ); ?></a>
                </div>
            <?php endif; ?>
        </header>
    </div>
    <?php
    return ob_get_clean();
}

function aeo_render_hero_svg_block( $attributes ) {
    $title = isset( $attributes['title'] ) && !empty( $attributes['title'] ) ? $attributes['title'] : get_the_title();
    $subtitle = isset( $attributes['subtitle'] ) ? $attributes['subtitle'] : '';
    $ctaText = isset( $attributes['ctaText'] ) ? $attributes['ctaText'] : '';
    $ctaUrl = isset( $attributes['ctaUrl'] ) ? $attributes['ctaUrl'] : '#';
    $align = isset( $attributes['align'] ) ? $attributes['align'] : '';
    $svgUrl = isset( $attributes['svgUrl'] ) ? $attributes['svgUrl'] : '';

    $align_class = $align ? ' align' . $align : '';

    ob_start();
    ?>
    <div class="wp-block-aeo-hero-svg<?php echo esc_attr( $align_class ); ?>">
        <?php if ( ! empty( $svgUrl ) ) : ?>
            <div class="aeo-hero-custom-svg" style="background-image: url(<?php echo esc_url( $svgUrl ); ?>); background-size: cover; background-position: center; position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1;"></div>
        <?php else : ?>
            <!-- Inline SVG pattern overlay for LCP and CLS optimization (glowing warm-amber floating bananas) -->
            <svg class="aeo-hero-svg-pattern" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" width="100%" height="100%" preserveAspectRatio="xMidYMid slice">
                <g fill="none" stroke="rgba(251, 191, 36, 0.15)" stroke-width="2">
                    <path class="banana-vector-1" d="M100,80 C130,110 140,150 110,180 C95,150 80,110 100,80 Z" style="transform-origin: 115px 130px;" />
                    <path class="banana-vector-2" d="M600,250 C630,220 650,180 630,150 C610,180 580,220 600,250 Z" style="transform-origin: 615px 200px;" />
                    <path class="banana-vector-1" d="M200,300 C220,320 230,340 210,360 C200,340 190,320 200,300 Z" style="transform-origin: 205px 330px;" />
                    <path class="banana-vector-2" d="M700,70 C720,50 730,30 710,10 C700,30 690,50 700,70 Z" style="transform-origin: 705px 40px;" />
                </g>
            </svg>
        <?php endif; ?>

        <header class="aeo-hero-gradient-header">
            <h1><?php echo esc_html( $title ); ?></h1>
            <?php if ( $subtitle ) : ?>
                <p class="aeo-hero-gradient-subtitle"><?php echo esc_html( $subtitle ); ?></p>
            <?php endif; ?>
            <?php if ( $ctaText ) : ?>
                <div class="aeo-hero-gradient-cta">
                    <a href="<?php echo esc_url( $ctaUrl ); ?>" class="aeo-hero-gradient-cta-btn"><?php echo esc_html( $ctaText ); ?></a>
                </div>
            <?php endif; ?>
        </header>
    </div>
    <?php
    return ob_get_clean();
}

function aeo_render_nav_block( $attributes ) {
    $brandText = isset( $attributes['brandText'] ) ? $attributes['brandText'] : 'aeo-copilot';
    $links     = isset( $attributes['links'] ) ? $attributes['links'] : array();
    $ctaText   = isset( $attributes['ctaText'] ) ? $attributes['ctaText'] : 'Take a Tour';
    $ctaUrl    = isset( $attributes['ctaUrl'] ) ? $attributes['ctaUrl'] : '#tour';

    // When rendered as a per-page block, just return empty since the global nav handles it.
    // This prevents duplicate nav bars.
    return '';
}

/* ================================================================
 * GLOBAL NAVIGATION — renders on every frontend page automatically
 * ================================================================ */

/**
 * Returns the global nav settings, merging saved options with defaults.
 */
function aeo_get_global_nav_settings() {
    $defaults = array(
        'brandText' => 'aeo-copilot',
        'links'     => array(
            array( 'label' => 'Features',  'url' => '#features' ),
            array( 'label' => 'Solutions', 'url' => '#solutions' ),
            array( 'label' => 'Pricing',   'url' => '#pricing' ),
            array( 'label' => 'Blog',      'url' => '#blog' ),
        ),
        'ctaText'   => 'Take a Tour',
        'ctaUrl'    => '#tour',
    );

    $saved = get_option( 'aeo_global_nav_settings', array() );
    return wp_parse_args( $saved, $defaults );
}

/**
 * Dynamically resolves navigation menu items from WordPress.
 * Checks classic menus, FSE wp_navigation post types, and falls back to default settings.
 */
function aeo_get_dynamic_nav_links() {
    // 1. Try Classic WordPress Menus
    $locations = get_nav_menu_locations();
    if ( isset( $locations['primary'] ) && ! empty( $locations['primary'] ) ) {
        $menu = wp_get_nav_menu_object( $locations['primary'] );
        if ( $menu ) {
            $menu_items = wp_get_nav_menu_items( $menu->term_id );
            if ( ! empty( $menu_items ) ) {
                $links = array();
                foreach ( $menu_items as $item ) {
                    $links[] = array(
                        'label' => $item->title,
                        'url'   => $item->url,
                    );
                }
                return $links;
            }
        }
    } else {
        // Fallback: search all classic menus for the first one that actually contains items
        $menus = wp_get_nav_menus();
        foreach ( $menus as $menu ) {
            $menu_items = wp_get_nav_menu_items( $menu->term_id );
            if ( ! empty( $menu_items ) ) {
                $links = array();
                foreach ( $menu_items as $item ) {
                    $links[] = array(
                        'label' => $item->title,
                        'url'   => $item->url,
                    );
                }
                return $links;
            }
        }
    }

    // 2. Try FSE Block Navigation Post Types
    $nav_posts = get_posts( array(
        'post_type'      => 'wp_navigation',
        'post_status'    => 'publish',
        'posts_per_page' => 1,
    ) );
    if ( ! empty( $nav_posts ) ) {
        $nav_post = $nav_posts[0];
        $blocks = parse_blocks( $nav_post->post_content );
        $links = aeo_parse_nav_blocks( $blocks );
        if ( ! empty( $links ) ) {
            return $links;
        }
    }

    // 3. Fallback to global options / defaults
    $settings = aeo_get_global_nav_settings();
    return $settings['links'];
}

/**
 * Helper to parse Gutenberg navigation blocks recursively.
 */
function aeo_parse_nav_blocks( $blocks ) {
    $links = array();
    foreach ( $blocks as $block ) {
        if ( $block['blockName'] === 'core/navigation-link' && isset( $block['attrs']['label'] ) ) {
            $links[] = array(
                'label' => $block['attrs']['label'],
                'url'   => $block['attrs']['url'] ?? '#',
            );
        } elseif ( $block['blockName'] === 'core/page-list' ) {
            // Dynamically fetch all published pages
            $pages = get_pages( array( 'post_status' => 'publish' ) );
            foreach ( $pages as $page ) {
                // Skip navigation and draft-like landing page post types
                if ( stripos( $page->post_title, 'Navigation' ) !== false ) {
                    continue;
                }
                $links[] = array(
                    'label' => $page->post_title,
                    'url'   => get_permalink( $page->ID ),
                );
            }
        } elseif ( ! empty( $block['innerBlocks'] ) ) {
            $links = array_merge( $links, aeo_parse_nav_blocks( $block['innerBlocks'] ) );
        }
    }
    return $links;
}

/**
 * Render the global nav bar on every frontend page via wp_body_open.
 */
function aeo_render_global_nav() {
    // Only render on the frontend, not in the admin/editor
    if ( is_admin() ) {
        return;
    }

    $settings  = aeo_get_global_nav_settings();
    $brandText = $settings['brandText'];
    $links     = aeo_get_dynamic_nav_links();
    $ctaText   = $settings['ctaText'];
    $ctaUrl    = $settings['ctaUrl'];
    ?>
    <div class="wp-block-aeo-nav aeo-global-nav">
        <nav class="aeo-nav-bar" role="navigation" aria-label="Main navigation">
            <div class="aeo-nav-brand"><?php echo esc_html( $brandText ); ?></div>

            <ul class="aeo-nav-links">
                <?php foreach ( $links as $link ) : ?>
                    <li class="aeo-nav-link-item">
                        <a href="<?php echo esc_url( $link['url'] ); ?>"><?php echo esc_html( $link['label'] ); ?></a>
                    </li>
                <?php endforeach; ?>
            </ul>

            <div class="aeo-nav-cta-wrap">
                <a href="<?php echo esc_url( $ctaUrl ); ?>" class="aeo-nav-cta-btn"><?php echo esc_html( $ctaText ); ?></a>
            </div>

            <div class="aeo-nav-burger" aria-label="Toggle menu" role="button" tabindex="0">
                <span></span><span></span><span></span>
            </div>
        </nav>

        <!-- Mobile drawer overlay -->
        <div class="aeo-nav-drawer" aria-hidden="true">
            <button class="aeo-nav-drawer-close" aria-label="Close menu">&times;</button>
            <?php foreach ( $links as $link ) : ?>
                <a href="<?php echo esc_url( $link['url'] ); ?>" class="aeo-nav-drawer-link"><?php echo esc_html( $link['label'] ); ?></a>
            <?php endforeach; ?>
            <a href="<?php echo esc_url( $ctaUrl ); ?>" class="aeo-nav-drawer-cta"><?php echo esc_html( $ctaText ); ?></a>
        </div>
    </div>
    <?php
}
add_action( 'wp_body_open', 'aeo_render_global_nav' );

/**
 * Globally enqueue nav CSS and JS on every frontend page.
 */
function aeo_enqueue_global_nav_assets() {
    if ( is_admin() ) {
        return;
    }

    $build_dir = __DIR__ . '/build/nav';

    // Enqueue the frontend style
    if ( file_exists( $build_dir . '/style-index.css' ) ) {
        wp_enqueue_style(
            'aeo-global-nav-style',
            plugins_url( 'build/nav/style-index.css', __FILE__ ),
            array(),
            filemtime( $build_dir . '/style-index.css' )
        );
    }

    // Enqueue the view script (scroll handler + mobile drawer toggle)
    if ( file_exists( $build_dir . '/view.js' ) ) {
        wp_enqueue_script(
            'aeo-global-nav-view',
            plugins_url( 'build/nav/view.js', __FILE__ ),
            array(),
            filemtime( $build_dir . '/view.js' ),
            true // load in footer
        );
    }
}
add_action( 'wp_enqueue_scripts', 'aeo_enqueue_global_nav_assets' );

/**
 * REST API endpoint to update global nav settings.
 * POST /wp-json/aeo/v1/nav-settings  { brandText, links, ctaText, ctaUrl }
 */
function aeo_register_nav_rest_routes() {
    register_rest_route( 'aeo/v1', '/nav-settings', array(
        'methods'             => 'GET',
        'callback'            => function() {
            return rest_ensure_response( aeo_get_global_nav_settings() );
        },
        'permission_callback' => '__return_true',
    ) );

    register_rest_route( 'aeo/v1', '/nav-settings', array(
        'methods'             => 'POST',
        'callback'            => function( $request ) {
            $params = $request->get_json_params();
            $current = aeo_get_global_nav_settings();

            if ( isset( $params['brandText'] ) ) {
                $current['brandText'] = sanitize_text_field( $params['brandText'] );
            }
            if ( isset( $params['links'] ) && is_array( $params['links'] ) ) {
                $current['links'] = array_map( function( $link ) {
                    return array(
                        'label' => sanitize_text_field( $link['label'] ?? '' ),
                        'url'   => esc_url_raw( $link['url'] ?? '#' ),
                    );
                }, $params['links'] );
            }
            if ( isset( $params['ctaText'] ) ) {
                $current['ctaText'] = sanitize_text_field( $params['ctaText'] );
            }
            if ( isset( $params['ctaUrl'] ) ) {
                $current['ctaUrl'] = esc_url_raw( $params['ctaUrl'] );
            }

            update_option( 'aeo_global_nav_settings', $current );
            return rest_ensure_response( $current );
        },
        'permission_callback' => function() {
            return current_user_can( 'manage_options' );
        },
    ) );
}
add_action( 'rest_api_init', 'aeo_register_nav_rest_routes' );

function aeo_render_footer_block( $attributes ) {
    // Return empty when rendered as a per-page block to let the global footer handle it.
    return '';
}

/* ================================================================
 * GLOBAL FOOTER — renders at the bottom of every page automatically
 * ================================================================ */

/**
 * Returns global footer settings, merging options with defaults.
 */
function aeo_get_global_footer_settings() {
    $defaults = array(
        'brandText' => 'aeo-copilot',
        'description' => 'Intelligent marketing automation and agentic search optimization for high-growth enterprises.',
        'column1Title' => 'Platform',
        'column1Links' => array(
            array( 'label' => 'Features', 'url' => '#features' ),
            array( 'label' => 'Solutions', 'url' => '#solutions' ),
            array( 'label' => 'Pricing', 'url' => '#pricing' ),
            array( 'label' => 'Security', 'url' => '#security' )
        ),
        'column2Title' => 'Resources',
        'column2Links' => array(
            array( 'label' => 'Documentation', 'url' => '#docs' ),
            array( 'label' => 'API Reference', 'url' => '#api' ),
            array( 'label' => 'AEO Guide', 'url' => '#aeo-guide' ),
            array( 'label' => 'Community', 'url' => '#community' )
        ),
        'column3Title' => 'Company',
        'column3Links' => array(
            array( 'label' => 'About Us', 'url' => '#about' ),
            array( 'label' => 'Careers', 'url' => '#careers' ),
            array( 'label' => 'Contact', 'url' => '#contact' ),
            array( 'label' => 'Privacy Policy', 'url' => '#privacy' )
        ),
        'statusText' => 'System Status: All Agents Operational',
        'copyrightText' => '© 2026 Sonnet and Prose. All rights reserved.'
    );

    $saved = get_option( 'aeo_global_footer_settings', array() );
    return wp_parse_args( $saved, $defaults );
}

/**
 * Render the global footer bar on every frontend page via wp_footer.
 */
function aeo_render_global_footer() {
    if ( is_admin() ) {
        return;
    }

    $settings = aeo_get_global_footer_settings();
    ?>
    <footer class="wp-block-aeo-footer">
        <div class="aeo-footer-grid">
            <div class="footer-col brand-col">
                <h3 class="brand-logo"><?php echo esc_html( $settings['brandText'] ); ?></h3>
                <p class="brand-desc"><?php echo esc_html( $settings['description'] ); ?></p>
            </div>
            <div class="footer-col">
                <h4><?php echo esc_html( $settings['column1Title'] ); ?></h4>
                <ul>
                    <?php foreach ( $settings['column1Links'] as $link ) : ?>
                        <li><a href="<?php echo esc_url( $link['url'] ); ?>"><?php echo esc_html( $link['label'] ); ?></a></li>
                    <?php endforeach; ?>
                </ul>
            </div>
            <div class="footer-col">
                <h4><?php echo esc_html( $settings['column2Title'] ); ?></h4>
                <ul>
                    <?php foreach ( $settings['column2Links'] as $link ) : ?>
                        <li><a href="<?php echo esc_url( $link['url'] ); ?>"><?php echo esc_html( $link['label'] ); ?></a></li>
                    <?php endforeach; ?>
                </ul>
            </div>
            <div class="footer-col">
                <h4><?php echo esc_html( $settings['column3Title'] ); ?></h4>
                <ul>
                    <?php foreach ( $settings['column3Links'] as $link ) : ?>
                        <li><a href="<?php echo esc_url( $link['url'] ); ?>"><?php echo esc_html( $link['label'] ); ?></a></li>
                    <?php endforeach; ?>
                </ul>
            </div>
        </div>
        <div class="aeo-footer-bottom">
            <p class="copyright"><?php echo esc_html( $settings['copyrightText'] ); ?></p>
            <div class="status-badge">
                <span class="pulse-indicator"></span>
                <span class="status-txt"><?php echo esc_html( $settings['statusText'] ); ?></span>
            </div>
        </div>
    </footer>
    <?php
}
add_action( 'wp_footer', 'aeo_render_global_footer' );

/**
 * Globally enqueue footer CSS.
 */
function aeo_enqueue_global_footer_assets() {
    if ( is_admin() ) {
        return;
    }

    $build_dir = __DIR__ . '/build/footer';

    if ( file_exists( $build_dir . '/style-index.css' ) ) {
        wp_enqueue_style(
            'aeo-global-footer-style',
            plugins_url( 'build/footer/style-index.css', __FILE__ ),
            array(),
            filemtime( $build_dir . '/style-index.css' )
        );
    }
}
add_action( 'wp_enqueue_scripts', 'aeo_enqueue_global_footer_assets' );

/**
 * REST API routes for global footer settings.
 */
function aeo_register_footer_rest_routes() {
    register_rest_route( 'aeo/v1', '/footer-settings', array(
        'methods'             => 'GET',
        'callback'            => function() {
            return rest_ensure_response( aeo_get_global_footer_settings() );
        },
        'permission_callback' => '__return_true',
    ) );

    register_rest_route( 'aeo/v1', '/footer-settings', array(
        'methods'             => 'POST',
        'callback'            => function( $request ) {
            $params = $request->get_json_params();
            $current = aeo_get_global_footer_settings();

            if ( isset( $params['brandText'] ) ) {
                $current['brandText'] = sanitize_text_field( $params['brandText'] );
            }
            if ( isset( $params['description'] ) ) {
                $current['description'] = sanitize_text_field( $params['description'] );
            }
            if ( isset( $params['column1Title'] ) ) {
                $current['column1Title'] = sanitize_text_field( $params['column1Title'] );
            }
            if ( isset( $params['column2Title'] ) ) {
                $current['column2Title'] = sanitize_text_field( $params['column2Title'] );
            }
            if ( isset( $params['column3Title'] ) ) {
                $current['column3Title'] = sanitize_text_field( $params['column3Title'] );
            }
            if ( isset( $params['statusText'] ) ) {
                $current['statusText'] = sanitize_text_field( $params['statusText'] );
            }
            if ( isset( $params['copyrightText'] ) ) {
                $current['copyrightText'] = sanitize_text_field( $params['copyrightText'] );
            }

            // Map and sanitize links array
            $sanitize_links = function( $links ) {
                if ( ! is_array( $links ) ) return array();
                return array_map( function( $link ) {
                    return array(
                        'label' => sanitize_text_field( $link['label'] ?? '' ),
                        'url'   => esc_url_raw( $link['url'] ?? '#' ),
                    );
                }, $links );
            };

            if ( isset( $params['column1Links'] ) ) {
                $current['column1Links'] = $sanitize_links( $params['column1Links'] );
            }
            if ( isset( $params['column2Links'] ) ) {
                $current['column2Links'] = $sanitize_links( $params['column2Links'] );
            }
            if ( isset( $params['column3Links'] ) ) {
                $current['column3Links'] = $sanitize_links( $params['column3Links'] );
            }

            update_option( 'aeo_global_footer_settings', $current );
            return rest_ensure_response( $current );
        },
        'permission_callback' => function() {
            return current_user_can( 'manage_options' );
        },
    ) );
}
add_action( 'rest_api_init', 'aeo_register_footer_rest_routes' );

function aeo_render_form_block( $attributes ) {
    $formTitle    = isset( $attributes['formTitle'] ) ? $attributes['formTitle'] : 'Request a Tour';
    $formSubtitle = isset( $attributes['formSubtitle'] ) ? $attributes['formSubtitle'] : 'Fill out the form below.';
    $submitText   = isset( $attributes['submitText'] ) ? $attributes['submitText'] : 'Send Request';
    $fields       = isset( $attributes['fields'] ) ? $attributes['fields'] : array();

    ob_start();
    ?>
    <div id="aeo-contact-section" class="wp-block-aeo-form">
        <header class="aeo-form-header">
            <h3><?php echo esc_html( $formTitle ); ?></h3>
            <p><?php echo esc_html( $formSubtitle ); ?></p>
        </header>
        <form class="aeo-form">
            <?php foreach ( $fields as $i => $field ) :
                $fieldId = 'aeo_field_' . esc_attr( $i ) . '_' . esc_attr( $field['id'] ?? '' );
                $required = ! empty( $field['required'] ) ? 'required' : '';
                $type = esc_attr( $field['type'] ?? 'text' );
                $label = esc_html( $field['label'] ?? '' );
                $placeholder = esc_attr( $field['placeholder'] ?? '' );
                ?>
                <div class="form-group">
                    <label for="<?php echo $fieldId; ?>">
                        <?php echo $label; ?>
                        <?php if ( $required ) : ?>
                            <span class="required-star">*</span>
                        <?php endif; ?>
                    </label>

                    <?php if ( $type === 'textarea' ) : ?>
                        <textarea id="<?php echo $fieldId; ?>" name="<?php echo esc_attr( $field['id'] ?? '' ); ?>" placeholder="<?php echo $placeholder; ?>" <?php echo $required; ?>></textarea>

                    <?php elseif ( $type === 'select' ) : ?>
                        <select id="<?php echo $fieldId; ?>" name="<?php echo esc_attr( $field['id'] ?? '' ); ?>" <?php echo $required; ?>>
                            <option value="">Choose an option...</option>
                            <?php
                            $options = array_map( 'trim', explode( ',', $field['options'] ?? '' ) );
                            foreach ( $options as $opt ) :
                                if ( empty( $opt ) ) continue;
                                ?>
                                <option value="<?php echo esc_attr( $opt ); ?>"><?php echo esc_html( $opt ); ?></option>
                            <?php endforeach; ?>
                        </select>

                    <?php elseif ( $type === 'file' ) : ?>
                        <input type="file" id="<?php echo $fieldId; ?>" name="<?php echo esc_attr( $field['id'] ?? '' ); ?>" <?php echo $required; ?> />

                    <?php else : ?>
                        <input type="<?php echo $type; ?>" id="<?php echo $fieldId; ?>" name="<?php echo esc_attr( $field['id'] ?? '' ); ?>" placeholder="<?php echo $placeholder; ?>" <?php echo $required; ?> />

                    <?php endif; ?>
                </div>
            <?php endforeach; ?>

            <div class="form-submit-wrap">
                <button type="submit" class="aeo-form-submit-btn"><?php echo esc_html( $submitText ); ?></button>
            </div>
        </form>
    </div>
    <?php
    return ob_get_clean();
}

function aeo_render_alert_block( $attributes ) {
    $type        = isset( $attributes['type'] ) ? $attributes['type'] : 'info';
    $message     = isset( $attributes['message'] ) ? $attributes['message'] : '';
    $dismissible = ! empty( $attributes['dismissible'] );

    $alert_icons = array(
        'success' => '<svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
        'info'    => '<svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
        'warning' => '<svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        'error'   => '<svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="#f87171" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'
    );

    $icon = isset( $alert_icons[ $type ] ) ? $alert_icons[ $type ] : $alert_icons['info'];

    ob_start();
    ?>
    <div class="aeo-alert-banner <?php echo esc_attr( $type ); ?>">
        <div class="alert-body">
            <?php echo $icon; ?>
            <div class="alert-content">
                <?php echo wp_kses_post( $message ); ?>
            </div>
        </div>
        <?php if ( $dismissible ) : ?>
            <button type="button" class="alert-close" aria-label="Dismiss alert">&times;</button>
        <?php endif; ?>
    </div>
    <?php
    return ob_get_clean();
}

function aeo_render_calculator_block( $attributes ) {
    $title           = isset( $attributes['title'] ) ? $attributes['title'] : 'Calculate Your Automation Savings';
    $subtitle        = isset( $attributes['subtitle'] ) ? $attributes['subtitle'] : 'Adjust the parameters below.';
    $hourlyRate      = isset( $attributes['hourlyRate'] ) ? intval( $attributes['hourlyRate'] ) : 85;
    $manualHours     = isset( $attributes['manualHours'] ) ? intval( $attributes['manualHours'] ) : 25;
    $multiplier      = isset( $attributes['multiplier'] ) ? floatval( $attributes['multiplier'] ) : 0.8;
    $maintenanceCost = isset( $attributes['maintenanceCost'] ) ? intval( $attributes['maintenanceCost'] ) : 2500;
    $ctaText         = isset( $attributes['ctaText'] ) ? $attributes['ctaText'] : 'Get Started';
    $ctaUrl          = isset( $attributes['ctaUrl'] ) ? $attributes['ctaUrl'] : '#';

    $weeklySavings   = round( $manualHours * $hourlyRate * $multiplier );
    $annualSavings   = round( ( $weeklySavings * 52 ) - $maintenanceCost );
    $hoursReclaimed  = round( $manualHours * 52 * $multiplier );

    ob_start();
    ?>
    <div class="wp-block-aeo-calculator" data-maintenance="<?php echo esc_attr( $maintenanceCost ); ?>">
        <header class="aeo-calc-header">
            <h4><?php echo esc_html( $title ); ?></h4>
            <p><?php echo esc_html( $subtitle ); ?></p>
        </header>

        <div class="aeo-calc-grid">
            <!-- Controls Column -->
            <div class="calc-sliders-wrap">
                <div class="calc-slider-group">
                    <label>Weekly Manual Hours: <span class="val-hours"><?php echo $manualHours; ?> hrs</span></label>
                    <input type="range" class="slider-hours" min="1" max="168" value="<?php echo $manualHours; ?>" />
                </div>
                <div class="calc-slider-group">
                    <label>Average Hourly Rate: <span class="val-rate">$<?php echo $hourlyRate; ?>/hr</span></label>
                    <input type="range" class="slider-rate" min="10" max="300" value="<?php echo $hourlyRate; ?>" />
                </div>
                <div class="calc-slider-group">
                    <label>Efficiency Multiplier: <span class="val-efficiency"><?php echo round($multiplier * 100); ?>%</span></label>
                    <input type="range" class="slider-efficiency" min="10" max="100" value="<?php echo round($multiplier * 100); ?>" />
                </div>
            </div>

            <!-- Results Column -->
            <div class="calc-results-wrap">
                <div class="result-metric highlight">
                    <span class="metric-label">Estimated Net Annual Savings</span>
                    <span class="metric-value metric-annual-savings">$<?php echo number_format( $annualSavings ); ?></span>
                </div>
                <div class="result-secondary">
                    <div class="result-metric">
                        <span class="metric-label">Weekly Savings</span>
                        <span class="metric-value metric-weekly-savings">$<?php echo number_format( $weeklySavings ); ?></span>
                    </div>
                    <div class="result-metric">
                        <span class="metric-label">Hours Reclaimed / Yr</span>
                        <span class="metric-value metric-hours-reclaimed"><?php echo number_format( $hoursReclaimed ); ?> hrs</span>
                    </div>
                </div>
                <div class="calc-cta-wrap">
                    <a href="<?php echo esc_url( $ctaUrl ); ?>" class="calc-cta-btn"><?php echo esc_html( $ctaText ); ?></a>
                </div>
            </div>
        </div>
    </div>
    <?php
    return ob_get_clean();
}

function aeo_render_metrics_grid_block( $attributes ) {
    $columns = isset( $attributes['columns'] ) ? intval( $attributes['columns'] ) : 3;
    $metrics = isset( $attributes['metrics'] ) ? $attributes['metrics'] : array();
    $outerBgColor = isset( $attributes['outerBgColor'] ) ? $attributes['outerBgColor'] : '';
    $innerBgColor = isset( $attributes['innerBgColor'] ) ? $attributes['innerBgColor'] : '';

    $outer_style = $outerBgColor ? ' style="background-color: ' . esc_attr( $outerBgColor ) . ';"' : '';
    $inner_style = $innerBgColor ? ' style="background-color: ' . esc_attr( $innerBgColor ) . ';"' : '';

    ob_start();
    ?>
    <div class="wp-block-aeo-metrics-grid"<?php echo $outer_style; ?>>
        <div class="aeo-metrics-grid-container cols-<?php echo esc_attr( $columns ); ?>">
            <?php foreach ( $metrics as $metric ) :
                $badgeText = isset( $metric['badgeText'] ) ? $metric['badgeText'] : '';
                $value     = isset( $metric['value'] ) ? $metric['value'] : '';
                $label     = isset( $metric['label'] ) ? $metric['label'] : '';
                ?>
                <div class="aeo-metric-card"<?php echo $inner_style; ?>>
                    <?php if ( ! empty( $badgeText ) ) : ?>
                        <div class="aeo-metric-badge-wrap">
                            <span class="badge-dot"></span>
                            <span class="badge-text"><?php echo esc_html( $badgeText ); ?></span>
                        </div>
                    <?php endif; ?>

                    <div class="aeo-metric-value-text">
                        <?php echo esc_html( $value ); ?>
                    </div>

                    <p class="aeo-metric-label-text">
                        <?php echo esc_html( $label ); ?>
                    </p>
                </div>
            <?php endforeach; ?>
        </div>
    </div>
    <?php
    return ob_get_clean();
}

function aeo_render_workflow_block( $attributes ) {
    $activeColor  = isset( $attributes['activeColor'] ) ? $attributes['activeColor'] : '#f59e0b';
    $steps        = isset( $attributes['steps'] ) ? $attributes['steps'] : array();
    $outerBgColor = isset( $attributes['outerBgColor'] ) ? $attributes['outerBgColor'] : '';
    $innerBgColor = isset( $attributes['innerBgColor'] ) ? $attributes['innerBgColor'] : '';
    $columns      = isset( $attributes['columns'] ) ? intval( $attributes['columns'] ) : 3;

    $outer_bg_style = $outerBgColor ? ' background-color: ' . esc_attr( $outerBgColor ) . ';' : '';
    $inner_bg_style = $innerBgColor ? ' style="background-color: ' . esc_attr( $innerBgColor ) . ';"' : '';

    ob_start();
    ?>
    <div class="wp-block-aeo-workflow" style="--active-color: <?php echo esc_attr( $activeColor ); ?>;<?php echo $outer_bg_style; ?>">
        <div class="aeo-workflow-timeline cols-<?php echo esc_attr( $columns ); ?>">
            <?php foreach ( $steps as $index => $step ) :
                $number      = isset( $step['number'] ) ? $step['number'] : sprintf( '%02d', $index + 1 );
                $title       = isset( $step['title'] ) ? $step['title'] : '';
                $description = isset( $step['description'] ) ? $step['description'] : '';
                $activeClass = ( $index === 0 ) ? 'active' : '';
                ?>
                <div class="aeo-workflow-step">
                    <div class="aeo-step-node <?php echo $activeClass; ?>">
                        <?php echo esc_html( $number ); ?>
                    </div>
                    <div class="aeo-step-card <?php echo $activeClass; ?>"<?php echo $inner_bg_style; ?>>
                        <h5><?php echo esc_html( $title ); ?></h5>
                        <p><?php echo esc_html( $description ); ?></p>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
    </div>
    <?php
    return ob_get_clean();
}

function aeo_render_media_showcase_block( $attributes ) {
    $title        = isset( $attributes['title'] ) ? $attributes['title'] : 'What Our Clients Say';
    $subtitle     = isset( $attributes['subtitle'] ) ? $attributes['subtitle'] : '';
    $ctaText      = isset( $attributes['ctaText'] ) ? $attributes['ctaText'] : '';
    $ctaUrl       = isset( $attributes['ctaUrl'] ) ? $attributes['ctaUrl'] : '#';
    $outerBgColor = isset( $attributes['outerBgColor'] ) ? $attributes['outerBgColor'] : '';
    $innerBgColor = isset( $attributes['innerBgColor'] ) ? $attributes['innerBgColor'] : '';
    $imageLoading = isset( $attributes['imageLoading'] ) ? $attributes['imageLoading'] : 'lazy';
    $testimonials = isset( $attributes['testimonials'] ) ? $attributes['testimonials'] : array();

    $outer_bg_style = $outerBgColor ? ' background-color: ' . esc_attr( $outerBgColor ) . ';' : '';
    $inner_bg_style = $innerBgColor ? ' style="background-color: ' . esc_attr( $innerBgColor ) . ';"' : '';
    $align          = isset( $attributes['align'] ) ? $attributes['align'] : '';
    $align_class    = $align ? ' align' . $align : '';

    // Programmatically generate JSON-LD schema for SEO/AEO entity disambiguation
    $reviews_schema = array(
        '@context'        => 'https://schema.org',
        '@type'           => 'ItemList',
        'name'            => $title,
        'itemListElement' => array()
    );

    ob_start();
    ?>
    <div class="wp-block-aeo-media-showcase<?php echo esc_attr( $align_class ); ?>" style="<?php echo $outer_bg_style; ?>">
        <div class="aeo-showcase-header">
            <?php if ( ! empty( $title ) ) : ?>
                <h2><?php echo esc_html( $title ); ?></h2>
            <?php endif; ?>
            <?php if ( ! empty( $subtitle ) ) : ?>
                <p><?php echo esc_html( $subtitle ); ?></p>
            <?php endif; ?>
        </div>

        <div class="aeo-showcase-slider-container">
            <div class="aeo-showcase-grid">
                <?php
                foreach ( $testimonials as $index => $item ) :
                    $quote         = isset( $item['quote'] ) ? $item['quote'] : '';
                    $expandedQuote = isset( $item['expandedQuote'] ) ? $item['expandedQuote'] : '';
                    $author        = isset( $item['author'] ) ? $item['author'] : '';
                    $role          = isset( $item['role'] ) ? $item['role'] : '';
                    $imageUrl      = isset( $item['imageUrl'] ) ? $item['imageUrl'] : '';
                    $imageAlt      = isset( $item['imageAlt'] ) ? $item['imageAlt'] : 'Avatar';
                    $authorUrl     = isset( $item['authorUrl'] ) ? $item['authorUrl'] : '';
                    $companyUrl    = isset( $item['companyUrl'] ) ? $item['companyUrl'] : '';

                    // Add item to structured data list
                    $full_review_text = $quote . ( ! empty( $expandedQuote ) ? ' ' . $expandedQuote : '' );
                    $review_node = array(
                        '@type'        => 'Review',
                        'position'     => $index + 1,
                        'author' => array(
                            '@type' => 'Person',
                            'name'  => $author
                        ),
                        'reviewBody' => $full_review_text
                    );

                    if ( ! empty( $authorUrl ) ) {
                        $review_node['author']['sameAs'] = $authorUrl;
                    }

                    if ( ! empty( $role ) ) {
                        $review_node['author']['worksFor'] = array(
                            '@type' => 'Organization',
                            'name'  => $role
                        );
                        if ( ! empty( $companyUrl ) ) {
                            $review_node['author']['worksFor']['url'] = $companyUrl;
                        }
                    }

                    $reviews_schema['itemListElement'][] = $review_node;
                    ?>
                    <div class="aeo-showcase-card"<?php echo $inner_bg_style; ?>>
                        <div class="aeo-showcase-quote-wrap">
                            <p class="quote-text">&#8220;<?php echo esc_html( $quote ); ?>&#8221;</p>
                        </div>

                        <?php if ( ! empty( $expandedQuote ) ) : ?>
                            <div class="aeo-showcase-expandable-section">
                                <p class="expanded-quote-text"><?php echo esc_html( $expandedQuote ); ?></p>
                            </div>
                            <button class="expand-toggle-btn">
                                <span class="btn-text">Read Full Story</span>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                    <polyline points="6 9 12 15 18 9"></polyline>
                                </svg>
                            </button>
                        <?php endif; ?>

                        <div class="aeo-showcase-author-wrap">
                            <?php if ( ! empty( $imageUrl ) ) : ?>
                                <div class="avatar-img-wrap">
                                    <img src="<?php echo esc_url( $imageUrl ); ?>" alt="<?php echo esc_attr( $imageAlt ); ?>" loading="<?php echo esc_attr( $imageLoading ); ?>" decoding="async" />
                                </div>
                            <?php endif; ?>
                            <div class="author-text-meta">
                                <h6>
                                    <?php if ( ! empty( $authorUrl ) ) : ?>
                                        <a href="<?php echo esc_url( $authorUrl ); ?>" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: none;"><?php echo esc_html( $author ); ?></a>
                                    <?php else : ?>
                                        <?php echo esc_html( $author ); ?>
                                    <?php endif; ?>
                                </h6>
                                <span>
                                    <?php if ( ! empty( $companyUrl ) ) : ?>
                                        <a href="<?php echo esc_url( $companyUrl ); ?>" target="_blank" rel="noopener noreferrer" style="color: #60a5fa; text-decoration: none;"><?php echo esc_html( $role ); ?></a>
                                    <?php else : ?>
                                        <?php echo esc_html( $role ); ?>
                                    <?php endif; ?>
                                </span>
                            </div>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>

            <button class="slider-nav-btn prev-btn" aria-label="Previous Testimonial">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
            </button>
            <button class="slider-nav-btn next-btn" aria-label="Next Testimonial">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </button>
        </div>

        <?php if ( ! empty( $ctaText ) ) : ?>
            <div class="aeo-showcase-cta-wrap">
                <a href="<?php echo esc_url( $ctaUrl ); ?>" class="aeo-showcase-cta-btn"><?php echo esc_html( $ctaText ); ?></a>
            </div>
        <?php endif; ?>

        <script type="application/ld+json">
        <?php echo wp_json_encode( $reviews_schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT ); ?>
        </script>
    </div>
    <?php
    return ob_get_clean();
}

/**
 * Automatically outputs any custom AEO schema injected via post/page metadata
 * into the frontend HTML header.
 */
function aeo_render_meta_json_ld_schema() {
    if ( ! is_singular() ) {
        return;
    }

    $schema_json = get_post_meta( get_the_ID(), 'aeo_schema_json', true );
    if ( ! empty( $schema_json ) ) {
        $decoded = json_decode( $schema_json, true );
        if ( json_last_error() === JSON_ERROR_NONE && ! empty( $decoded ) ) {
            ?>
            <script type="application/ld+json">
            <?php echo wp_json_encode( $decoded, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT ); ?>
            </script>
            <?php
        }
    }
}
add_action( 'wp_head', 'aeo_render_meta_json_ld_schema' );

/**
 * Programmatically generates and outputs FAQPage JSON-LD schema in the footer
 * by parsing all Gutenberg FAQ accordion blocks on the current page.
 */
function aeo_render_faq_json_ld_schema() {
    if ( ! is_singular() ) {
        return;
    }

    $post = get_post();
    if ( ! $post || ! has_block( 'aeo-custom-blocks/faq', $post->post_content ) ) {
        return;
    }

    $blocks = parse_blocks( $post->post_content );
    $faq_items = array();

    // Recursive helper to find FAQ blocks
    $find_faqs = function( $blocks_list ) use ( &$find_faqs, &$faq_items ) {
        foreach ( $blocks_list as $block ) {
            if ( $block['blockName'] === 'aeo-custom-blocks/faq' ) {
                $q = $block['attrs']['question'] ?? '';
                $a = $block['attrs']['answer'] ?? '';
                if ( ! empty( $q ) && ! empty( $a ) ) {
                    $faq_items[] = array(
                        'question' => wp_strip_all_tags( $q ),
                        'answer'   => wp_strip_all_tags( $a )
                    );
                }
            }
            if ( ! empty( $block['innerBlocks'] ) ) {
                $find_faqs( $block['innerBlocks'] );
            }
        }
    };

    $find_faqs( $blocks );

    if ( empty( $faq_items ) ) {
        return;
    }

    $faq_schema = array(
        '@context'   => 'https://schema.org',
        '@type'      => 'FAQPage',
        'mainEntity' => array()
    );

    foreach ( $faq_items as $item ) {
        $faq_schema['mainEntity'][] = array(
            '@type'          => 'Question',
            'name'           => $item['question'],
            'acceptedAnswer' => array(
                '@type' => 'Answer',
                'text'  => $item['answer']
            )
        );
    }

    ?>
    <script type="application/ld+json">
    <?php echo wp_json_encode( $faq_schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT ); ?>
    </script>
    <?php
}
add_action( 'wp_footer', 'aeo_render_faq_json_ld_schema' );

/**
 * Force bust browser caching of Media Showcase assets (frontend & editor)
 */
add_action( 'wp_enqueue_scripts', 'aeo_force_bust_showcase_assets', 100 );
function aeo_force_bust_showcase_assets() {
    wp_deregister_style( 'aeo-custom-blocks-media-showcase-style' );
    wp_register_style(
        'aeo-custom-blocks-media-showcase-style',
        plugins_url( 'build/media-showcase/style-index.css', __FILE__ ),
        array(),
        time()
    );

    wp_deregister_script( 'aeo-custom-blocks-media-showcase-view-script' );
    wp_register_script(
        'aeo-custom-blocks-media-showcase-view-script',
        plugins_url( 'build/media-showcase/view.js', __FILE__ ),
        array(),
        time(),
        true
    );
}

add_action( 'enqueue_block_editor_assets', 'aeo_force_bust_editor_assets', 100 );
function aeo_force_bust_editor_assets() {
    wp_deregister_script( 'aeo-custom-blocks-media-showcase-editor-script' );
    wp_register_script(
        'aeo-custom-blocks-media-showcase-editor-script',
        plugins_url( 'build/media-showcase/index.js', __FILE__ ),
        array( 'wp-blocks', 'wp-element', 'wp-editor', 'wp-components', 'wp-data', 'wp-compose' ),
        time(),
        true
    );
}
