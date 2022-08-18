from pathlib import Path
from re import match

from num2words import num2words

from modules.CardType import CardType
from modules.Debug import log

class OlivierTitleCard(CardType):
    """
    This class describes a type of ImageMaker that produces title cards in the
    style of those designed by Reddit user /u/Olivier_286.
    """

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'olivier'
    SW_REF_DIRECTORY = Path(__file__).parent / 'ref' / 'star_wars'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 16,   # Character count to begin splitting titles
        'max_line_count': 5,    # Maximum number of lines a title can take up
        'top_heavy': True,      # This class uses top heavy titling
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Montserrat-Bold.ttf').resolve())
    TITLE_COLOR = 'white'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'EPISODE {episode_number}'
    EPISODE_TEXT_COLOR = 'white'#'#CFCFCF'
    EPISODE_PREFIX_FONT = SW_REF_DIRECTORY / 'HelveticaNeue.ttc'
    EPISODE_NUMBER_FONT = SW_REF_DIRECTORY / 'HelveticaNeue-Bold.ttf'

    """Whether this class uses season titles for the purpose of archives"""
    USES_SEASON_TITLE = False

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Olivier Style'

    """Paths to intermediate files created for this card"""
    __RESIZED_SOURCE = CardType.TEMP_DIR / 'resized_source.png'

    __slots__ = ('source_file', 'output_file', 'title', 'hide_episode_text', 
                 'episode_prefix', 'episode_text', 'font', 'title_color',
                 'episode_text_color', 'font_size', 'stroke_width', 'kerning',
                 'vertical_shift', 'interline_spacing', 'blur')

    
    def __init__(self, source: Path, output_file: Path, title: str,
                 episode_text: str, font: str, font_size:float,title_color: str,
                 stroke_width: float=1.0, vertical_shift: int=0,
                 interline_spacing: int=0, kerning: float=1.0,
                 episode_text_color: str=EPISODE_TEXT_COLOR, blur: bool=False,
                 **kwargs) -> None:
        """
        Initialize this TitleCard object. This primarily just stores instance
        variables for later use in `create()`. It also determines the episode
        prefix text.

        Args:
            source: Source image to base the card on.
            output_file: Output file where to create the card.
            title: Title text to add to created card.
            episode_text: Episode text to add to created card.
            font: Font name or path (as string) to use for episode title.
            font_size: Scalar to apply to title font size.
            title_color: Color to use for title text.
            stroke_width: Scalar to apply to black stroke of the title text.
            vertical_shift: Pixel count to adjust the title vertical offset by.
            interline_spacing: Pixel count to adjust title interline spacing by.
            kerning: Scalar to apply to kerning of the title text.
            episode_text_color: Color to use for the episode text.
            blur: Whether to blur the source image.
            kwargs: Unused arguments.
        """
        
        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__()

        # Store source and output file
        self.source_file = source
        self.output_file = output_file

        # Store attributes of the text
        self.title = self.image_magick.escape_chars(title.upper())
        self.hide_episode_text = len(episode_text) == 0
        self.episode_prefix = None
        
        # Determine episode prefix
        # Modify episode text to remove "Episode"-like text, replace numbers
        if (not self.hide_episode_text
            and (groups := match(r'^(.*?)\s*(\d+)\s*$',
                                 episode_text)) is not None):
            pre, number = groups.groups()
            self.episode_prefix = pre.upper()
            episode_text = num2words(int(number)).upper()
        else:
            episode_text = episode_text.upper()
        self.episode_text = self.image_magick.escape_chars(episode_text)

        # Font customizations
        self.font = font
        self.title_color = title_color
        self.episode_text_color = episode_text_color
        self.font_size = font_size
        self.stroke_width = stroke_width
        self.vertical_shift = vertical_shift
        self.interline_spacing = interline_spacing
        self.kerning = kerning

        # Store blur flag
        self.blur = blur


    def __resize_source(self, source: Path) -> Path:
        """
        Resize the given source image. Optionally blur the image as well.
        
        Args:
            source: The source image to modify.
        
        Returns:
            Path to the created image.
        """

        command = ' '.join([
            f'convert "{source.resolve()}"',
            f'+profile "*"',
            f'-gravity center',
            f'-resize "{self.TITLE_CARD_SIZE}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            f'"{self.__RESIZED_SOURCE.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.__RESIZED_SOURCE


    def __add_title_text(self) -> list[str]:
        """
        Get the ImageMagick commands to add the episode title text to an image.
        
        Returns:
            List of ImageMagick commands.
        """

        font_size = 124 * self.font_size
        stroke_width = 6.0 * self.stroke_width
        kerning = 0.5 * self.kerning
        interline_spacing = -20 + self.interline_spacing

        return [
            f'\( -font "{self.font}"',
            f'-gravity northwest',
            f'-pointsize {font_size}',
            f'-kerning {kerning}',
            f'-interline-spacing {interline_spacing}',
            f'-fill black',
            f'-stroke black',
            f'-strokewidth {stroke_width}',
            f'-annotate +320+785 "{self.title}" \)',
            f'\( -fill "{self.title_color}"',
            f'-stroke "{self.title_color}"',
            f'-strokewidth 0',
            f'-annotate +320+785 "{self.title}" \)',
        ]


    def __add_episode_prefix(self) -> list[str]:
        """
        Get the ImageMagick commands to add the episode prefix text to an image.

        Returns:
            List of ImageMagick commands.
        """

        if self.episode_prefix is None:
            return []

        return [
            f'-gravity west',
            f'-font "{self.EPISODE_PREFIX_FONT.resolve()}"',
            f'-pointsize 53',
            f'-kerning 19',
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 4',
            f'-annotate +325-140 "{self.episode_prefix}"',
            f'-fill "{self.episode_text_color}"',
            f'-stroke "{self.episode_text_color}"',
            f'-strokewidth 0',
            f'-annotate +325-140 "{self.episode_prefix}"',
        ]


    def __add_episode_number_text(self) -> list[str]:
        """
        Get the ImageMagick commands to add the episode number text to an image.

        Returns:
            List of ImageMagick commands.
        """

        # Get variable horizontal offset based of episode prefix
        text_offset = {'EPISODE': 400, 'CHAPTER': 400, 'PART': 250}
        if self.episode_prefix is None:
            offset = 0
        elif self.episode_prefix in text_offset.keys():
            offset = text_offset[self.episode_prefix]
        else:
            offset_per_char = text_offset['EPISODE'] / len('EPISODE')
            offset = offset_per_char * len(self.episode_prefix)

        return [
            f'-gravity west',
            f'-font "{self.EPISODE_NUMBER_FONT.resolve()}"',
            f'-pointsize 53',
            f'-kerning 19',
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 5',
            f'-annotate +{325+offset}-140 "{self.episode_text}"',
            f'-fill "{self.episode_text_color}"',
            f'-stroke "{self.episode_text_color}"',
            f'-strokewidth 1',
            f'-annotate +{325+offset}-140 "{self.episode_text}"',
        ]


    def __add_only_title(self, resized_source: Path) -> Path:
        """
        Add only the title to the given image.
        
        Args:
            resized_source: Source image to add title to.

        Returns:
            Path to the created image (the output file).
        """

        command = ' '.join([
            f'convert "{gradient_source.resolve()}"',
            *self.__add_title_text(),
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.output_file


    def __add_all_text(self, gradient_source: Path) -> Path:
        """
        Add the title, episode prefix, and episode text to the given image.
        
        Args:
            resized_source: Source image to add title to.

        Returns:
            Path to the created image (the output file).
        """

        command = ' '.join([
            f'convert "{gradient_source.resolve()}"',
            *self.__add_title_text(),
            *self.__add_episode_prefix(),
            *self.__add_episode_number_text(),
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)

        return self.output_file


    @staticmethod
    def is_custom_font(font: 'Font') -> bool:
        """
        Determine whether the given arguments represent a custom font for this
        card.

        Args:
            font: The Font being evaluated.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return ((font.file != OlivierTitleCard.TITLE_FONT)
            or (font.size != 1.0)
            or (font.color != OlivierTitleCard.TITLE_COLOR)
            or (font.vertical_shift != 0)
            or (font.interline_spacing != 0)
            or (font.kerning != 1.0)
            or (font.stroke_width != 1.0))


    @staticmethod
    def is_custom_season_titles(*args, **kwargs) -> bool:
        """
        Determine whether the given attributes constitute custom or generic
        season titles.

        Args:
            args and kwargs: Generic arguments.

        Returns:
            False, as custom season titles aren't used.
        """

        return False


    def create(self) -> None:
        """Create the title card as defined by this object."""

        # Resize the source image
        resized = self.__resize_source(self.source_file)

        # Add text to resized image
        if self.hide_episode_text:
            self.__add_only_title(resized)
        else:
            self.__add_all_text(resized)

        # Delete all intermediate images
        self.image_magick.delete_intermediate_images(resized)
