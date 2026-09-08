extern crate alloc;
use nextcore_core::boot_picker as view;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Pixel(u32);
impl view::Pixel for Pixel {
    fn rgb(r: u8, g: u8, b: u8) -> Self {
        Self(((r as u32) << 16) | ((g as u32) << 8) | b as u32)
    }
}
#[test]
fn navigation_wraps_and_boots_only_current_selection() {
    use view::{Action::*, Update};
    let mut n = 0;
    assert_eq!(view::navigate(&mut n, 3, Previous), Update::Redraw);
    assert_eq!(n, 2);
    assert_eq!(view::navigate(&mut n, 3, Next), Update::Redraw);
    assert_eq!(n, 0);
    assert_eq!(view::navigate(&mut n, 3, Last), Update::Redraw);
    assert_eq!(view::navigate(&mut n, 3, Boot), Update::Boot(2));
    assert_eq!(view::navigate(&mut n, 3, First), Update::Redraw);
    assert_eq!(view::navigate(&mut n, 3, None), Update::Unchanged);
    assert_eq!(view::navigate(&mut n, 3, Cancel), Update::Cancel);
    assert_eq!(view::navigate(&mut n, 0, Boot), Update::Cancel);
    n = 4;
    assert_eq!(view::navigate(&mut n, 3, Boot), Update::Cancel);
}
#[test]
fn renders_resolutions_and_scrolls_all_entries_without_changing_identity() {
    let names = vec!["macOS"; 64];
    for (width, height) in [(640, 480), (800, 600), (1024, 768), (1920, 1080)] {
        let first =
            view::render::<Pixel>(width, height, &names, "NextCore Test", 0, false).unwrap();
        let last =
            view::render::<Pixel>(width, height, &names, "NextCore Test", 63, false).unwrap();
        assert_eq!(first.len(), width * height);
        assert_ne!(first, last);
        assert!(first.iter().any(|p| p.0 == 0xb9edce));
        assert_eq!(first[0].0, 0x08090b);
    }
}
#[test]
fn allocation_limits_invalid_selection_and_starting_state_are_explicit() {
    for (w, h) in [(usize::MAX, 2), (640, 400), (4097, 2160), (640, 2161)] {
        assert_eq!(
            view::render::<Pixel>(w, h, &["EFI"], "", 0, false),
            Err(view::ViewError::Dimensions)
        );
    }
    assert_eq!(
        view::render::<Pixel>(640, 480, &[], "", 0, false),
        Err(view::ViewError::Selection)
    );
    assert_eq!(
        view::render::<Pixel>(640, 480, &["EFI"], "", 1, false),
        Err(view::ViewError::Selection)
    );
    let idle = view::render::<Pixel>(800, 600, &["EFI"], "", 0, false).unwrap();
    assert_ne!(
        idle,
        view::render::<Pixel>(800, 600, &["EFI"], "", 0, true).unwrap()
    );
}
#[test]
fn unsupported_glyphs_and_long_text_stay_inside_canvas() {
    assert_eq!(
        view::render::<Pixel>(640, 480, &["한글"], "", 0, false).unwrap(),
        view::render::<Pixel>(640, 480, &["??"], "", 0, false).unwrap()
    );
    assert_eq!(
        view::render::<Pixel>(640, 480, &[&"x".repeat(4096)], "\u{1b}[2J", 0, false)
            .unwrap()
            .len(),
        640 * 480
    );
}
