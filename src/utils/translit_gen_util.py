from hma_translit.seq2seq.evaluators.reporter import get_decoded_words
from hma_translit.seq2seq.model_utils import load_checkpoint, model_builder, setup_optimizers
from hma_translit.seq2seq.prepare_data import load_vocab
from hma_translit.utils.arguments import PARSER


def init_model(vocabfile, translit_model):
    args = {'iters': 20, 'maxsteps': 500000, 'batch_size': 1, 'seed': 42,
            'restore': 'si.model', 'profile': False, 'save': None,
            'lang': 'hi', 'wdim': 50, 'hdim': 20, 'cell': 'gru',
            'wdrop': 0.0, 'lr': 0.001, 'clip': None, 'optimizer': 'adam',
            'extra': None, 'nat_or_eng': 'both', 'evalfreq': 500, 'logfreq': 100,
            'patience': 10, 'reduction_factor': 0.1, 'beam_width': 1,
            'norm_by_length': False, 'single_token': True, 'max_output_length': 75,
            'ftrain': None, 'ftest': None, 'frac': 1.0, 'dump': None, 'bidi': True,
            'batch_first': True, 'mono': True, 'interactive': True, 'outfile': None,
            'vocabfile': 'si_data.vocab', 'aligned_file': None}

    fr_lang, en_lang = load_vocab(vocabfile=vocabfile)
    encoder, decoder, evaler = model_builder(args=args, fr_lang=fr_lang, en_lang=en_lang)
    enc_opt, dec_opt, enc_sch, dec_sch = setup_optimizers(args=args, encoder=encoder, decoder=decoder)

    load_checkpoint(encoder=encoder, decoder=decoder,
                    enc_opt=enc_opt, dec_opt=dec_opt,
                    ckpt_path=translit_model)

    return evaler


def is_num(text):
    for character in text:
        if character not in '0123456789_sth-':
            return False
    return True


def predict_translit(surface, evaler):
    surface = " ".join(list(surface))

    x, y, weight, is_eng = surface, None, 1.0, False
    decoded_outputs = evaler.infer_on_example(sentence=x)
    scores_and_words = get_decoded_words(decoded_outputs)
    decoded_words = [w for s, w in scores_and_words]
    # scores = [s for s, w in scores_and_words]
    return decoded_words


def phrase_translit(phrase_str, concepts, evaler, spell, translit_dict):
    if '#' in phrase_str or '@' in phrase_str:
        return []

    outputs = []
    for concept in concepts:
        if concept[0] in phrase_str:
            outputs.append(concept[1])
            phrase_str = phrase_str.replace(concept[0], ' ')

    phrase_str = phrase_str.replace('  ', ' ')
    new_phrase = phrase_str.split()

    tokens = []
    for item in new_phrase:
        if len(item):
            flag = True
            if '-' in item:
                tokens += item.split('-')
                flag = False
            if '.' in item:
                tokens += item.split('.')
                flag = False

            if flag:
                tokens += [item]

    outputs = []
    for token in tokens:
        if token in translit_dict:
            outputs.append(translit_dict[token])
        else:
            outputs.append(''.join(predict_translit(token, evaler)[0].split()))

    output_str = ' '.join(outputs)
    if spell is not None:
        corrected = spell.correction(output_str)
    else:
        corrected = output_str

    if output_str == corrected:
        return [output_str]
    else:
        return [output_str, corrected]
