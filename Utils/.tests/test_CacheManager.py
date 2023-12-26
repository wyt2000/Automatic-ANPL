from Utils import CacheManager
import shutil

def test_CacheManager():
    with CacheManager('anpl_test_cache') as m:
        m.save('solution', 'It is a test solution', 1, [1,2,3], 'ab', True)
        m.save('synthesizer', 'It is an anpl code', 'anpl')
        assert m.load('solution', 1, [1,2,3], 'ab', True) == 'It is a test solution'
        assert m.load('synthesizer', 'anpl') == 'It is an anpl code'

    with CacheManager('anpl_test_cache') as m:
        assert m.load('solution', 1, [1,2,3], 'ab', True) == 'It is a test solution'

    with CacheManager('anpl_test_cache', True) as m:
        assert m.load('solution', 1, [1,2,3], 'ab', True) is None
        m.save('solution', 'It is a test solution', 1, [1,2,3], 'ab', True)
        m.save('solution', 'It is another test solution', 'anpl')
        m.save('synthesizer', 'It is an anpl code', 'anpl')
        assert m.load('solution', 'anpl') == 'It is another test solution'
        assert m.load('synthesizer', 'anpl') == 'It is an anpl code'

    try:
        with CacheManager('anpl_test_cache', True) as m:
            m.save('solution', 'It is a test solution', 1, [1,2,3], 'ab', True)
            raise Exception
            m.save('solution', 'It is another test solution', 'anpl')
            m.save('synthesizer', 'It is an anpl code', 'anpl')
    except Exception:
        pass

    with CacheManager('anpl_test_cache') as m:
        assert m.load('solution', 1, [1,2,3], 'ab', True) == 'It is a test solution'
        assert m.load('solution', 'anpl') is None

    shutil.rmtree('anpl_test_cache')

